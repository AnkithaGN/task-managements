# ---------------------------------------------------------------
# tasks/views.py
# Pages of the tasks app: dashboard, list, detail, create, edit,
# delete, complete/pending toggle and history.
# EVERY view is login-protected and only touches the user's OWN tasks.
# ---------------------------------------------------------------

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Case, Count, IntegerField, Q, Value, When
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.text import Truncator
from django.views.decorators.http import require_POST

from .forms import TaskFilterForm, TaskForm
from .models import Activity, Category, Priority, Status, Task, TaskActivity

# How many tasks to show on one page of "My tasks".
TASKS_PER_PAGE = 10
# How many history entries to show on one page of "History".
HISTORY_PER_PAGE = 15


def get_user_task(request, pk):
    """Return task <pk> only if it belongs to the logged-in user, else 404.

    This one helper is our AUTHORIZATION rule: another user's task
    behaves exactly like a task that does not exist.
    """
    return get_object_or_404(Task, pk=pk, owner=request.user)


def short_title(task_or_title, length=50):
    """Shorten long titles for messages: 'AAAA...AAA…' (max `length` characters)."""
    title = getattr(task_or_title, 'title', task_or_title)
    return Truncator(title).chars(length)


def log_activity(user, task, action):
    """Write one row to the History table."""
    TaskActivity.objects.create(owner=user, task=task, task_title=task.title, action=action)


@login_required
def home(request):
    """Dashboard: counts, completion progress, per-category summary, upcoming tasks."""
    today = timezone.localdate()
    my_tasks = Task.objects.filter(owner=request.user)

    # aggregate() = ONE database query that returns several totals.
    # Count('id', filter=Q(...)) counts only rows matching the condition.
    counts = my_tasks.aggregate(
        total=Count('id'),
        pending=Count('id', filter=Q(status=Status.PENDING)),
        completed=Count('id', filter=Q(status=Status.COMPLETED)),
        overdue=Count('id', filter=Q(status=Status.PENDING, due_date__lt=today)),
    )

    # Percentage of tasks completed (0 when there are no tasks: never divide by zero).
    if counts['total']:
        percent_done = round(counts['completed'] * 100 / counts['total'])
    else:
        percent_done = 0

    # annotate() = add a calculated number to EACH category.
    # tasks__owner follows the link from Category to its tasks (related_name='tasks').
    categories = Category.objects.annotate(
        total=Count('tasks', filter=Q(tasks__owner=request.user)),
        pending=Count('tasks', filter=Q(tasks__owner=request.user, tasks__status=Status.PENDING)),
        completed=Count('tasks', filter=Q(tasks__owner=request.user, tasks__status=Status.COMPLETED)),
    )

    # Next 5 pending tasks (soonest due date first, so overdue ones come first).
    upcoming = my_tasks.filter(status=Status.PENDING).select_related('category')[:5]

    return render(request, 'tasks/home.html', {
        'counts': counts,
        'percent_done': percent_done,
        'categories': categories,
        'upcoming': upcoming,
    })


def sort_tasks(tasks, sort):
    """Apply the chosen sort order. Unknown values fall back to due date."""
    if sort == '-due':
        return tasks.order_by('-due_date', 'title')
    if sort == 'title':
        return tasks.order_by('title')
    if sort == 'newest':
        return tasks.order_by('-created_at')
    if sort == 'priority':
        # Text sorts alphabetically (HIGH, LOW, MEDIUM), which is wrong for priority.
        # Case/When turns each priority into a number: High=0, Medium=1, Low=2.
        priority_rank = Case(
            When(priority=Priority.HIGH, then=Value(0)),
            When(priority=Priority.MEDIUM, then=Value(1)),
            When(priority=Priority.LOW, then=Value(2)),
            output_field=IntegerField(),
        )
        return tasks.order_by(priority_rank, 'due_date', 'title')
    return tasks.order_by('due_date', 'title')


@login_required
def task_list(request):
    """My tasks, with search, filters (any combination), sorting and pages."""
    # Start with ONLY this user's tasks. Every filter below narrows this further.
    tasks = Task.objects.filter(owner=request.user).select_related('category')

    # Filters arrive in the address: /tasks/?q=report&category=2&priority=HIGH&sort=title&page=2
    # request.GET holds them. The form validates them.
    filter_form = TaskFilterForm(request.GET)
    filter_form.is_valid()           # runs the checks; invalid values are left out
    data = filter_form.cleaned_data  # only the VALID filter values

    if data.get('q'):
        # icontains = "contains", ignoring upper/lower case.
        tasks = tasks.filter(title__icontains=data['q'])
    if data.get('category'):
        tasks = tasks.filter(category=data['category'])
    if data.get('priority'):
        tasks = tasks.filter(priority=data['priority'])
    if data.get('status'):
        tasks = tasks.filter(status=data['status'])

    tasks = sort_tasks(tasks, data.get('sort'))

    # Pagination: split the results into pages of TASKS_PER_PAGE.
    # get_page() is forgiving: ?page=abc or ?page=999 shows page 1 or the last page instead of an error.
    paginator = Paginator(tasks, TASKS_PER_PAGE)
    page_obj = paginator.get_page(request.GET.get('page'))

    # True if the user typed or chose any filter (used for the "no results" message).
    is_filtered = any(request.GET.get(name) for name in ['q', 'category', 'priority', 'status'])

    return render(request, 'tasks/task_list.html', {
        'page_obj': page_obj,
        'filter_form': filter_form,
        'is_filtered': is_filtered,
    })


@login_required
def task_detail(request, pk):
    task = get_user_task(request, pk)
    return render(request, 'tasks/task_detail.html', {'task': task})


@login_required
def task_create(request):
    if request.method == 'POST':
        form = TaskForm(request.POST)
        if form.is_valid():
            # Build the task but do not save yet...
            task = form.save(commit=False)
            # ...set the owner from the logged-in user (never from the form)...
            task.owner = request.user
            # ...then save it to the database.
            task.save()
            log_activity(request.user, task, Activity.CREATED)
            messages.success(request, f'Task "{short_title(task)}" was created.')
            return redirect('task_detail', pk=task.pk)
    else:
        form = TaskForm()
    return render(request, 'tasks/task_form.html', {'form': form, 'is_edit': False})


@login_required
def task_update(request, pk):
    task = get_user_task(request, pk)
    if request.method == 'POST':
        # instance=task -> update THIS task instead of creating a new one.
        form = TaskForm(request.POST, instance=task)
        if form.is_valid():
            # has_changed() is False when the user pressed Save without changing anything.
            changed = form.has_changed()
            form.save()
            if changed:
                log_activity(request.user, task, Activity.UPDATED)
            messages.success(request, f'Task "{short_title(task)}" was updated.')
            return redirect('task_detail', pk=task.pk)
    else:
        # Show the form filled with the task's current values.
        form = TaskForm(instance=task)
    return render(request, 'tasks/task_form.html', {'form': form, 'is_edit': True, 'task': task})


@login_required
def task_delete(request, pk):
    task = get_user_task(request, pk)
    if request.method == 'POST':
        # Only a POST (the confirm button) deletes.
        title = short_title(task)
        # Record the deletion FIRST, while the task still exists.
        # When the task is then deleted, on_delete=SET_NULL keeps this history row.
        log_activity(request.user, task, Activity.DELETED)
        task.delete()
        messages.success(request, f'Task "{title}" was deleted. You can still see it in History.')
        return redirect('task_list')
    # GET -> show the "Are you sure?" page.
    return render(request, 'tasks/task_confirm_delete.html', {'task': task})


@login_required
@require_POST
def task_toggle_status(request, pk):
    task = get_user_task(request, pk)

    # Flip the status: Pending <-> Completed.
    if task.status == Status.PENDING:
        task.status = Status.COMPLETED
        action = Activity.COMPLETED
    else:
        task.status = Status.PENDING
        action = Activity.REOPENED
    task.save(update_fields=['status', 'updated_at'])
    log_activity(request.user, task, action)

    messages.success(request, f'Task "{short_title(task)}" marked as {task.get_status_display()}.')

    # Return to the list if the button was on the list page, else to the detail page.
    # We only accept the fixed word "list" (never a full address) so nobody can
    # use this button to redirect users to another website.
    if request.POST.get('next') == 'list':
        return redirect('task_list')
    return redirect('task_detail', pk=task.pk)


@login_required
def history(request):
    """Everything that happened to the user's tasks, newest first."""
    # Only THIS user's history. select_related('task') loads the linked task in the same query.
    activities = TaskActivity.objects.filter(owner=request.user).select_related('task')

    # Optional filter: /history/?action=DELETED  (invalid values are ignored)
    action = request.GET.get('action', '')
    if action in Activity.values:
        activities = activities.filter(action=action)
    else:
        action = ''

    page_obj = Paginator(activities, HISTORY_PER_PAGE).get_page(request.GET.get('page'))

    return render(request, 'tasks/history.html', {
        'page_obj': page_obj,
        'action': action,
        'actions': Activity.choices,
    })
