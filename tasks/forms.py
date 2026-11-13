# ---------------------------------------------------------------
# tasks/forms.py
# TaskForm:       create / edit a task, with the due-date rules.
# TaskFilterForm: search, filters and sort order on the "My tasks" page.
# ---------------------------------------------------------------

from django import forms
from django.utils import timezone

from .models import Category, Priority, Status, Task


class TaskForm(forms.ModelForm):
    """Create / edit a task. Owner and status are NOT editable here."""

    class Meta:
        model = Task
        # owner  -> set by the view from the logged-in user (security).
        # status -> changed only by the Complete / Pending button.
        fields = ['title', 'description', 'due_date', 'priority', 'category']
        widgets = {
            # type="date" shows a calendar picker in the browser.
            'due_date': forms.DateInput(attrs={'type': 'date'}, format='%Y-%m-%d'),
            'description': forms.Textarea(attrs={'rows': 4}),
        }

    def clean_due_date(self):
        due_date = self.cleaned_data['due_date']

        # "Today" in India time (TIME_ZONE = 'Asia/Kolkata').
        today = timezone.localdate()

        # Rule 5: editing an existing task and the date was NOT changed
        # -> keep it, even if it is now in the past.
        if self.instance.pk and due_date == self.instance.due_date:
            return due_date

        # Rules 3 and 4: today is allowed, earlier dates are not.
        if due_date < today:
            raise forms.ValidationError('Due date cannot be in the past.')

        return due_date


# Sort options: value in the address -> label shown in the dropdown.
SORT_CHOICES = [
    ('due', 'Due date (soonest first)'),
    ('-due', 'Due date (latest first)'),
    ('priority', 'Priority (high first)'),
    ('title', 'Title (A-Z)'),
    ('newest', 'Newest first'),
]


class TaskFilterForm(forms.Form):
    """Search, filters and sort. Every field is optional: empty = no filter."""

    # forms.Form (not ModelForm): it is not saved anywhere, it only validates the filters.
    q = forms.CharField(
        required=False,
        max_length=200,
        label='Search title',
    )
    # ModelChoiceField: the value must be the id of an existing Category.
    category = forms.ModelChoiceField(
        queryset=Category.objects.all(),
        required=False,
        empty_label='All categories',
    )
    # ChoiceField: the value must be one of these choices. '' = "All".
    priority = forms.ChoiceField(
        choices=[('', 'All priorities')] + Priority.choices,
        required=False,
    )
    status = forms.ChoiceField(
        choices=[('', 'All statuses')] + Status.choices,
        required=False,
    )
    # Sort order. Invalid values are ignored and the default (due date) is used.
    sort = forms.ChoiceField(
        choices=SORT_CHOICES,
        required=False,
        label='Sort by',
    )
