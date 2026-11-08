# ---------------------------------------------------------------
# tasks/migrations/0002_seed_categories.py
# DATA migration: inserts the 3 fixed categories into tasks_category.
# Runs automatically wherever "python manage.py migrate" runs
# (my laptop, test database, AWS), so the categories are never missing.
# ---------------------------------------------------------------

from django.db import migrations

# The fixed categories required by the project.
# CAPITAL letters = a constant (a value that should not change).
CATEGORY_NAMES = ['Personal', 'Work', 'Study']


# FORWARD: runs when we apply this migration (python manage.py migrate).
# Django passes "apps" and "schema_editor" in automatically.
def add_categories(apps, schema_editor):
    # Get the Category model AS IT WAS at this point in migration history.
    # Rule: in migrations, use apps.get_model(), never "from tasks.models import ...".
    Category = apps.get_model('tasks', 'Category')

    # Loop over the 3 names.
    for name in CATEGORY_NAMES:
        # Find the category if it exists, otherwise create it.
        # Safe to run twice: never creates duplicates.
        Category.objects.get_or_create(name=name)


# REVERSE: runs only if we ever UNDO this migration.
def remove_categories(apps, schema_editor):
    Category = apps.get_model('tasks', 'Category')
    # Find categories whose name is in our list, and delete them.
    Category.objects.filter(name__in=CATEGORY_NAMES).delete()


class Migration(migrations.Migration):

    # Run this AFTER migration 0001 (the table must exist first).
    dependencies = [
        ('tasks', '0001_initial'),
    ]

    # What this migration does: run our Python functions.
    # RunPython(forward_function, reverse_function)
    operations = [
        migrations.RunPython(add_categories, remove_categories),
    ]