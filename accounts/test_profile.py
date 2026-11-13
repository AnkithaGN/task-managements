# Automated tests for the profile picture. Run: python manage.py test accounts
import io
import shutil
import tempfile

from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from PIL import Image

from accounts.models import Profile

TEMP_MEDIA = tempfile.mkdtemp()   # uploads go to a throw-away folder, not the real media/


def make_image(fmt='PNG', size=(60, 60)):
    buffer = io.BytesIO()
    Image.new('RGB', size, (99, 102, 241)).save(buffer, fmt)
    return buffer.getvalue()


@override_settings(MEDIA_ROOT=TEMP_MEDIA)
class ProfilePictureTests(TestCase):
    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA, ignore_errors=True)

    def setUp(self):
        self.user = User.objects.create_user('pic', 'pic@example.com', 'Strong#Pass123')
        self.client.force_login(self.user)
        self.base = {'first_name': 'Pic', 'last_name': 'User', 'email': 'pic@example.com'}

    def post(self, file=None, **extra):
        data = dict(self.base, **extra)
        if file is not None:
            data['avatar'] = file
        return self.client.post('/accounts/profile/edit/', data)

    def test_upload_valid_png(self):
        r = self.post(SimpleUploadedFile('me.png', make_image(), content_type='image/png'))
        self.assertEqual(r.status_code, 302)
        profile = Profile.objects.get(user=self.user)
        self.assertTrue(profile.avatar.name.startswith(f'avatars/user_{self.user.pk}/'))
        self.assertIn(profile.avatar.url, self.client.get('/accounts/profile/').content.decode())

    def test_reject_file_that_is_not_an_image(self):
        r = self.post(SimpleUploadedFile('evil.png', b'not really an image', content_type='image/png'))
        self.assertEqual(r.status_code, 200)
        self.assertFalse(Profile.objects.get(user=self.user).avatar)

    def test_reject_too_large_image(self):
        big = make_image('BMP', (1100, 1100))      # about 3.6 MB, and BMP is not allowed either
        r = self.post(SimpleUploadedFile('big.bmp', big, content_type='image/bmp'))
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, 'too large')

    def test_remove_picture(self):
        self.post(SimpleUploadedFile('me.png', make_image(), content_type='image/png'))
        r = self.post(**{'avatar-clear': 'on'})
        self.assertEqual(r.status_code, 302)
        self.assertFalse(Profile.objects.get(user=self.user).avatar)

    def test_profile_without_picture_shows_letter(self):
        page = self.client.get('/accounts/profile/').content.decode()
        self.assertIn('avatar-letter', page)
