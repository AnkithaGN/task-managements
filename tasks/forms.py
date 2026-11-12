# ---------------------------------------------------------------
# tasks/forms.py
# Form used to create and edit tasks, with the due-date rules.
# ---------------------------------------------------------------

from django import forms
from django.utils import timezone

from .models import Task


class TaskForm(forms.ModelForm):
    """Create / edit a task. Owner and status are NOT editable here."""

    class Meta:
        model = Task
        # Only these fields appear in the form.
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
        # self.instance.pk is None for a NEW task, and a number for an existing one.
        if self.instance.pk and due_date == self.instance.due_date:
            return due_date

        # Rules 3 and 4: today is allowed, earlier dates are not.
        if due_date < today:
            raise forms.ValidationError('Due date cannot be in the past.')

        return due_date