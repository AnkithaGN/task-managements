# ---------------------------------------------------------------
# tasks/admin.py
# Shows our models in Django Admin (http://127.0.0.1:8000/admin/).
# Only REGISTERED models appear in the admin.
# ---------------------------------------------------------------

from django.contrib import admin

# The dot means "from this same app folder" (tasks/models.py).
from .models import Category, Task


# @admin.register(Category) = "show the Category model in the admin,
# using the settings in the class below".
# (The @ line is called a DECORATOR: it adds behaviour to the class under it.)
@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    # Columns shown in the category list page.
    list_display = ['id', 'name']


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    # Columns shown in the task list page.
    list_display = ['title', 'owner', 'category', 'priority', 'status', 'due_date']

    # Filter boxes on the right side of the list page.
    list_filter = ['status', 'priority', 'category']

    # Adds a search box that searches task titles.
    search_fields = ['title']