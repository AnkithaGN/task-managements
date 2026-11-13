# Automated tests for the History feature. Run: python manage.py test tasks
import datetime
from django.contrib.auth.models import User
from django.test import TestCase
from tasks.models import Category, Task, TaskActivity


class HistoryTests(TestCase):
    def setUp(self):
        self.u1 = User.objects.create_user('h1', 'h1@example.com', 'Strong#Pass123')
        self.u2 = User.objects.create_user('h2', 'h2@example.com', 'Strong#Pass123')
        self.cat = Category.objects.get(name='Work')
        self.client.force_login(self.u1)
        self.today = datetime.date.today().isoformat()

    def make(self, title='History test'):
        r = self.client.post('/tasks/new/', {'title': title, 'description': '', 'due_date': self.today,
                                             'priority': 'HIGH', 'category': self.cat.pk})
        return Task.objects.get(pk=int(r['Location'].strip('/').split('/')[-1]))

    def test_full_lifecycle(self):
        t = self.make()
        data = {'title': 'History test 2', 'description': '', 'due_date': self.today, 'priority': 'HIGH', 'category': self.cat.pk}
        self.client.post(f'/tasks/{t.pk}/edit/', data)                 # changed -> UPDATED
        self.client.post(f'/tasks/{t.pk}/edit/', data)                 # unchanged -> nothing
        self.client.post(f'/tasks/{t.pk}/toggle/')                     # COMPLETED
        self.client.post(f'/tasks/{t.pk}/toggle/')                     # REOPENED
        self.client.post(f'/tasks/{t.pk}/delete/')                     # DELETED
        actions = list(TaskActivity.objects.filter(owner=self.u1).order_by('created_at', 'id').values_list('action', flat=True))
        self.assertEqual(actions, ['CREATED', 'UPDATED', 'COMPLETED', 'REOPENED', 'DELETED'])
        self.assertFalse(Task.objects.filter(pk=t.pk).exists())
        self.assertTrue(all(a.task is None for a in TaskActivity.objects.filter(owner=self.u1)))   # SET_NULL
        page = self.client.get('/history/').content.decode()
        self.assertIn('History test 2', page)
        self.assertIn('deleted-title', page)

    def test_filter_and_invalid_filter(self):
        t = self.make(); self.client.post(f'/tasks/{t.pk}/toggle/')
        self.assertEqual(self.client.get('/history/?action=COMPLETED').context['page_obj'].paginator.count, 1)
        self.assertEqual(self.client.get('/history/?action=HACK').context['page_obj'].paginator.count, 2)

    def test_other_user_cannot_see_history(self):
        self.make('Secret task of h1')
        self.client.force_login(self.u2)
        r = self.client.get('/history/')
        self.assertEqual(r.context['page_obj'].paginator.count, 0)
        self.assertNotIn('timeline-item', r.content.decode())

    def test_long_title_message_is_short(self):
        t = self.make('B' * 200)
        r = self.client.post(f'/tasks/{t.pk}/delete/', follow=True)
        msg = [str(m) for m in r.context['messages']][-1]
        self.assertLess(len(msg), 120)
        self.assertIn('History', msg)

    def test_logged_out_redirect(self):
        self.client.logout()
        r = self.client.get('/history/')
        self.assertEqual(r.status_code, 302)
        self.assertIn('/accounts/login/', r['Location'])
