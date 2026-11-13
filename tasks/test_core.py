# Automated regression tests for the core features. Run: python manage.py test
# Django creates a separate test database, runs these, then deletes it.
import datetime

from django.contrib.auth.models import User
from django.test import TestCase

from tasks.models import Category, Task

PASSWORD = 'Strong#Pass123'


class CoreTests(TestCase):
    def setUp(self):
        self.alice = User.objects.create_user('alice', 'alice@example.com', PASSWORD)
        self.bob = User.objects.create_user('bob', 'bob@example.com', PASSWORD)
        self.work = Category.objects.get(name='Work')
        self.study = Category.objects.get(name='Study')
        self.today = datetime.date.today()
        self.client.force_login(self.alice)

    def task(self, owner=None, **kw):
        data = dict(owner=owner or self.alice, title='Report', due_date=self.today,
                    priority='HIGH', category=self.work)
        data.update(kw)
        return Task.objects.create(**data)

    def form(self, **kw):
        data = {'title': 'New task', 'description': '', 'due_date': self.today.isoformat(),
                'priority': 'MEDIUM', 'category': self.work.pk}
        data.update(kw)
        return data

    # ---------- authentication ----------
    def test_categories_seeded(self):
        self.assertEqual(sorted(Category.objects.values_list('name', flat=True)), ['Personal', 'Study', 'Work'])

    def test_login_with_email_case_insensitive(self):
        self.client.logout()
        r = self.client.post('/accounts/login/', {'username': 'ALICE@example.com', 'password': PASSWORD})
        self.assertEqual(r.status_code, 302)

    def test_wrong_password_and_unknown_email_same_message(self):
        self.client.logout()
        r1 = self.client.post('/accounts/login/', {'username': 'alice@example.com', 'password': 'wrong'})
        r2 = self.client.post('/accounts/login/', {'username': 'nobody@example.com', 'password': 'wrong'})
        self.assertContains(r1, 'Incorrect email or password.')
        self.assertContains(r2, 'Incorrect email or password.')

    def test_register_duplicate_email_refused(self):
        self.client.logout()
        r = self.client.post('/accounts/register/', {'username': 'alice2', 'email': 'Alice@Example.com',
                                                     'password1': PASSWORD, 'password2': PASSWORD})
        self.assertContains(r, 'An account with this email already exists.')

    def test_protected_pages_redirect_to_login(self):
        self.client.logout()
        for path in ['/', '/tasks/', '/tasks/new/', '/history/', '/accounts/profile/', '/accounts/password/']:
            r = self.client.get(path)
            self.assertEqual(r.status_code, 302, path)
            self.assertIn('/accounts/login/', r['Location'])

    # ---------- create / validation ----------
    def test_create_task_today_ok(self):
        r = self.client.post('/tasks/new/', self.form())
        self.assertEqual(r.status_code, 302)
        self.assertEqual(Task.objects.get(title='New task').owner, self.alice)

    def test_past_due_date_refused(self):
        r = self.client.post('/tasks/new/', self.form(due_date=(self.today - datetime.timedelta(days=1)).isoformat()))
        self.assertContains(r, 'Due date cannot be in the past.')

    def test_edit_keeps_unchanged_past_date(self):
        t = self.task(due_date=self.today - datetime.timedelta(days=5))
        r = self.client.post(f'/tasks/{t.pk}/edit/', self.form(title='Renamed', due_date=t.due_date.isoformat()))
        self.assertEqual(r.status_code, 302)

    def test_required_fields(self):
        r = self.client.post('/tasks/new/', {'title': '', 'due_date': '', 'priority': '', 'category': ''})
        self.assertEqual(r.content.decode().count('This field is required.'), 4)

    def test_owner_field_injection_ignored(self):
        self.client.post('/tasks/new/', self.form(title='Injected', owner=self.bob.pk))
        self.assertEqual(Task.objects.get(title='Injected').owner, self.alice)

    # ---------- authorization (business rule 6) ----------
    def test_other_user_gets_404_everywhere(self):
        t = self.task(owner=self.bob, title='Bob secret')
        self.assertEqual(self.client.get(f'/tasks/{t.pk}/').status_code, 404)
        self.assertEqual(self.client.get(f'/tasks/{t.pk}/edit/').status_code, 404)
        self.assertEqual(self.client.post(f'/tasks/{t.pk}/edit/', self.form(title='HACKED')).status_code, 404)
        self.assertEqual(self.client.post(f'/tasks/{t.pk}/toggle/').status_code, 404)
        self.assertEqual(self.client.post(f'/tasks/{t.pk}/delete/').status_code, 404)
        t.refresh_from_db()
        self.assertEqual(t.title, 'Bob secret')
        self.assertNotContains(self.client.get('/tasks/'), 'Bob secret')

    def test_toggle_requires_post(self):
        t = self.task()
        self.assertEqual(self.client.get(f'/tasks/{t.pk}/toggle/').status_code, 405)

    def test_toggle_and_delete(self):
        t = self.task()
        self.client.post(f'/tasks/{t.pk}/toggle/')
        t.refresh_from_db()
        self.assertEqual(t.status, 'COMPLETED')
        self.client.post(f'/tasks/{t.pk}/delete/')
        self.assertFalse(Task.objects.filter(pk=t.pk).exists())

    # ---------- dashboard (business rule 8) ----------
    def test_dashboard_counts_match_database(self):
        self.task(title='A')
        self.task(title='B', status='COMPLETED')
        self.task(title='C', due_date=self.today - datetime.timedelta(days=2))
        self.task(owner=self.bob, title='Not mine')
        counts = self.client.get('/').context['counts']
        self.assertEqual(counts, {'total': 3, 'pending': 2, 'completed': 1, 'overdue': 1})

    # ---------- search, filters, sort, pagination ----------
    def test_search_and_combined_filters(self):
        self.task(title='Quarterly report')
        self.task(title='Read report', category=self.study, priority='LOW')
        self.task(title='Shopping', priority='LOW')
        titles = lambda q: sorted(t.title for t in self.client.get('/tasks/?' + q).context['page_obj'])
        self.assertEqual(titles('q=REPORT'), ['Quarterly report', 'Read report'])
        self.assertEqual(titles('q=report&priority=LOW'), ['Read report'])
        self.assertEqual(titles(f'category={self.study.pk}'), ['Read report'])
        self.assertEqual(titles('q=zzzz'), [])
        self.assertEqual(len(titles('priority=URGENT')), 3)   # invalid value ignored

    def test_sort_by_priority(self):
        self.task(title='Low one', priority='LOW')
        self.task(title='High one', priority='HIGH')
        self.task(title='Medium one', priority='MEDIUM')
        order = [t.priority for t in self.client.get('/tasks/?sort=priority').context['page_obj']]
        self.assertEqual(order, ['HIGH', 'MEDIUM', 'LOW'])

    def test_pagination_ten_per_page(self):
        for i in range(12):
            self.task(title=f'Task {i:02d}')
        page1 = self.client.get('/tasks/').context['page_obj']
        page2 = self.client.get('/tasks/?page=2').context['page_obj']
        self.assertEqual((len(page1), len(page2), page1.paginator.num_pages), (10, 2, 2))
        self.assertEqual(self.client.get('/tasks/?page=abc').status_code, 200)

    # ---------- profile and password ----------
    def test_profile_extra_fields_ignored(self):
        self.client.post('/accounts/profile/edit/', {'first_name': 'A', 'last_name': 'B', 'email': 'alice@example.com',
                                                     'is_superuser': 'on', 'username': 'admin'})
        self.alice.refresh_from_db()
        self.assertFalse(self.alice.is_superuser)
        self.assertEqual(self.alice.username, 'alice')

    def test_password_change_needs_old_password(self):
        r = self.client.post('/accounts/password/', {'old_password': 'wrong', 'new_password1': 'Another#Pass456',
                                                     'new_password2': 'Another#Pass456'})
        self.assertEqual(r.status_code, 200)
        r = self.client.post('/accounts/password/', {'old_password': PASSWORD, 'new_password1': 'Another#Pass456',
                                                     'new_password2': 'Another#Pass456'})
        self.assertEqual(r.status_code, 302)
        self.alice.refresh_from_db()
        self.assertTrue(self.alice.check_password('Another#Pass456'))
