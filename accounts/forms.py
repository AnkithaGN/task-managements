# ---------------------------------------------------------------
# accounts/forms.py
# Forms for registration, email login and profile editing.
# Forms validate user input ON THE SERVER before anything is saved.
# ---------------------------------------------------------------

from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm

from .models import Profile

User = get_user_model()

# Largest picture we accept (2 MB). Bigger files are refused with a message.
MAX_AVATAR_SIZE = 2 * 1024 * 1024
ALLOWED_IMAGE_TYPES = {'JPEG', 'PNG', 'WEBP', 'GIF'}


def email_taken(email, exclude_pk=None):
    """True if another account already uses this email (any upper/lower case)."""
    users = User.objects.filter(email__iexact=email)
    if exclude_pk is not None:
        # When editing a profile, the user's OWN current email is not a duplicate.
        users = users.exclude(pk=exclude_pk)
    return users.exists()


class RegisterForm(UserCreationForm):
    """Registration: username, email, password, password confirmation."""

    email = forms.EmailField(
        required=True,
        max_length=254,
        help_text='You will log in with this email.',
    )

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('username', 'email')

    def clean_email(self):
        email = self.cleaned_data['email'].strip().lower()
        if email_taken(email):
            raise forms.ValidationError('An account with this email already exists.')
        return email


class EmailLoginForm(AuthenticationForm):
    """Login form whose first box is an email address."""

    username = forms.EmailField(
        label='Email',
        widget=forms.EmailInput(attrs={'autofocus': True}),
    )

    error_messages = {
        **AuthenticationForm.error_messages,
        'invalid_login': 'Incorrect email or password.',
    }


class ProfileForm(forms.ModelForm):
    """Edit first name, last name and email. Username is not editable."""

    email = forms.EmailField(
        required=True,
        max_length=254,
        help_text='This is also your login email.',
    )

    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'email')

    def clean_email(self):
        email = self.cleaned_data['email'].strip().lower()
        # self.instance = the user being edited; their own email is allowed.
        if email_taken(email, exclude_pk=self.instance.pk):
            raise forms.ValidationError('An account with this email already exists.')
        return email


class AvatarForm(forms.ModelForm):
    """Upload, replace or remove the profile picture."""

    class Meta:
        model = Profile
        fields = ('avatar',)
        labels = {'avatar': 'Profile picture'}
        help_texts = {'avatar': 'JPG, PNG, WEBP or GIF, up to 2 MB.'}
        # accept="image/*" makes the file picker show images first (the server still checks).
        widgets = {'avatar': forms.ClearableFileInput(attrs={'accept': 'image/*'})}

    def clean_avatar(self):
        avatar = self.cleaned_data.get('avatar')
        # Only check NEW uploads (an existing saved picture has no .image attribute).
        if avatar and hasattr(avatar, 'image'):
            if avatar.size > MAX_AVATAR_SIZE:
                raise forms.ValidationError('The picture is too large. Please choose one up to 2 MB.')
            # ImageField already proved it is a real image; also check the format.
            if (avatar.image.format or '').upper() not in ALLOWED_IMAGE_TYPES:
                raise forms.ValidationError('Please upload a JPG, PNG, WEBP or GIF image.')
        return avatar
