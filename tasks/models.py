# ---------------------------------------------------------------
# tasks/models.py
# Describes the data of the Tasks app.
# Each class below becomes one table in PostgreSQL.
# ---------------------------------------------------------------

# Gives access to our project settings (we use it to find the User model).
from django.conf import settings

# Django's tools for building models: field types, Model, Q, constraints.
from django.db import models

# Today's date in India time (TIME_ZONE = 'Asia/Kolkata').
from django.utils import timezone


# ---------------------------------------------------------------
# FIXED CHOICE LISTS
# TextChoices = a fixed list of allowed values.
# Each line: NAME = 'value saved in database', 'label shown to users'
# ---------------------------------------------------------------

class Priority(models.TextChoices):
    LOW = 'LOW', 'Low'
    MEDIUM = 'MEDIUM', 'Medium'
    HIGH = 'HIGH', 'High'


class Status(models.TextChoices):
    PENDING = 'PENDING', 'Pending'
    COMPLETED = 'COMPLETED', 'Completed'


class Activity(models.TextChoices):
    """What happened to a task (used by the History page)."""
    CREATED = 'CREATED', 'Created'
    UPDATED = 'UPDATED', 'Updated'
    COMPLETED = 'COMPLETED', 'Completed'
    REOPENED = 'REOPENED', 'Reopened'
    DELETED = 'DELETED', 'Deleted'


# ---------------------------------------------------------------
# CATEGORY MODEL  ->  table "tasks_category"
# Holds the categories: Personal, Work, Study.
# ---------------------------------------------------------------

class Category(models.Model):  # inherits from models.Model, so Django makes it a table
    # Text column, max 50 characters. unique=True: no two categories can have the same name.
    name = models.CharField(max_length=50, unique=True)

    # Meta = settings ABOUT the table (not columns).
    class Meta:
        ordering = ['name']                 # list categories A-Z by default
        verbose_name_plural = 'categories'  # correct plural in Django Admin (not "Categorys")

    # How a category is shown as text, e.g. "Work" instead of "Category object (1)".
    def __str__(self):
        return self.name


# ---------------------------------------------------------------
# TASK MODEL  ->  table "tasks_task"
# One row = one task belonging to one user.
# Fields are REQUIRED by default unless blank=True is given.
# ---------------------------------------------------------------

class Task(models.Model):
    # Who owns this task. ForeignKey = stores the id of a row in another table (auth_user).
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,   # Django's User model (safe way to refer to it)
        on_delete=models.CASCADE,   # if the user is deleted, delete their tasks too
        related_name='tasks',       # lets us write: user.tasks.all()
    )

    # Required short text, max 200 characters.
    title = models.CharField(max_length=200)

    # Long text. blank=True makes it OPTIONAL (empty is saved as '').
    description = models.TextField(blank=True)

    # Required date (no time part).
    due_date = models.DateField()

    # Required. Must be one of LOW / MEDIUM / HIGH. No default, so the user must choose.
    priority = models.CharField(max_length=10, choices=Priority.choices)

    # Required link to a category (stored as category_id).
    category = models.ForeignKey(
        Category,
        on_delete=models.PROTECT,   # block deleting a category that still has tasks
        related_name='tasks',       # lets us write: category.tasks.all()
    )

    # PENDING or COMPLETED. New tasks start as PENDING automatically.
    status = models.CharField(
        max_length=10,
        choices=Status.choices,
        default=Status.PENDING,
    )

    # Set automatically ONCE, when the task is created.
    created_at = models.DateTimeField(auto_now_add=True)

    # Set automatically EVERY time the task is saved.
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        # Default sort: soonest due date first, then title A-Z.
        ordering = ['due_date', 'title']

        # CheckConstraint = a rule enforced by PostgreSQL itself.
        # Even if bad data skips our forms, the database refuses it.
        # Q(...) builds a condition.  ~Q(...) means NOT.
        constraints = [
            # priority must be one of: LOW, MEDIUM, HIGH
            models.CheckConstraint(
                condition=models.Q(priority__in=Priority.values),
                name='task_priority_valid',
            ),
            # status must be one of: PENDING, COMPLETED
            models.CheckConstraint(
                condition=models.Q(status__in=Status.values),
                name='task_status_valid',
            ),
            # title must NOT be empty text
            models.CheckConstraint(
                condition=~models.Q(title=''),
                name='task_title_not_empty',
            ),
        ]

    # How a task is shown as text: its title.
    def __str__(self):
        return self.title

    # @property = use it like a field: task.is_overdue (no brackets).
    # It is CALCULATED each time, not stored in the database (no migration needed).
    @property
    def is_overdue(self):
        """True when the task is still pending and its due date has passed."""
        return self.status == Status.PENDING and self.due_date < timezone.localdate()

    @property
    def days_left(self):
        """Whole days from today to the due date (negative = late)."""
        return (self.due_date - timezone.localdate()).days

    @property
    def due_label(self):
        """Friendly text such as 'Due today', 'Due in 3 days' or '2 days overdue'.

        Empty for completed tasks (a finished task is never late).
        """
        if self.status == Status.COMPLETED:
            return ''
        days = self.days_left
        if days == 0:
            return 'Due today'
        if days == 1:
            return 'Due tomorrow'
        if days > 1:
            return f'Due in {days} days'
        if days == -1:
            return '1 day overdue'
        return f'{-days} days overdue'


# ---------------------------------------------------------------
# TASK ACTIVITY MODEL  ->  table "tasks_taskactivity"
# One row = one thing that happened to a task (the History page).
# ---------------------------------------------------------------

class TaskActivity(models.Model):
    # Whose history this is. Deleting the user deletes their history.
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='task_activities',
    )

    # Link to the task. SET_NULL: when the task is DELETED, this row is KEPT
    # and only the link becomes empty (NULL). That is how deleted tasks stay in History.
    # null=True  -> the database column may be empty.
    # blank=True -> forms may leave it empty.
    task = models.ForeignKey(
        Task,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='activities',
    )

    # A copy of the title at that moment, so History still shows it after deletion.
    task_title = models.CharField(max_length=200)

    # What happened: Created / Updated / Completed / Reopened / Deleted.
    action = models.CharField(max_length=10, choices=Activity.choices)

    # When it happened (set automatically).
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']          # newest first
        verbose_name_plural = 'task activities'
        constraints = [
            models.CheckConstraint(
                condition=models.Q(action__in=Activity.values),
                name='taskactivity_action_valid',
            ),
        ]

    def __str__(self):
        return f'{self.get_action_display()}: {self.task_title}'
