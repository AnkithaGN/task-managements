# ---------------------------------------------------------------
# tasks/views.py
# Pages of the tasks app: dashboard, list, detail, create, edit,
# delete and complete/pending toggle.
# EVERY view is login-protected and only touches the user's OWN tasks.
# ---------------------------------------------------------------

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST
from .forms import TaskFilterForm, TaskForm
from .models import Category, Status, Task


def get_user_task(request, pk):
    """Return task <pk> only if it belongs to the logged-in user, else 404.

    This one helper is our AUTHORIZATION rule: another user's task
    behaves exactly like a task that does not exist.
    """
    return get_object_or_404(Task, pk=pk, owner=request.user)


@login_required
def home(request):
    """Dashboard: counts, per-category summary and upcoming tasks."""
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
        'categories': categories,
        'upcoming': upcoming,
    })


@login_required
def task_list(request):
    """My tasks, with search by title and filters (any combination)."""
    # Start with ONLY this user's tasks. Every filter below narrows this further.
    tasks = Task.objects.filter(owner=request.user).select_related('category')

    # Filters arrive in the address: /tasks/?q=report&category=2&priority=HIGH
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

    # True if the user typed or chose any filter (used for the "no results" message).
    is_filtered = any(request.GET.get(name) for name in ['q', 'category', 'priority', 'status'])

    return render(request, 'tasks/task_list.html', {
        'tasks': tasks,
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
            messages.success(request, f'Task "{task.title}" was created.')
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
            form.save()
            messages.success(request, f'Task "{task.title}" was updated.')
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
        title = task.title
        task.delete()
        messages.success(request, f'Task "{title}" was deleted.')
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
    else:
        task.status = Status.PENDING
    task.save(update_fields=['status', 'updated_at'])

    messages.success(request, f'Task "{task.title}" marked as {task.get_status_display()}.')

    # Return to the list if the button was on the list page, else to the detail page.
    # We only accept the fixed word "list" (never a full address) so nobody can
    # use this button to redirect users to another website.
    if request.POST.get('next') == 'list':
        return redirect('task_list')
    return redirect('task_detail', pk=task.pk)