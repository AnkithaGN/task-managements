# ---------------------------------------------------------------
# tasks/views.py
# Pages of the tasks app.
# ---------------------------------------------------------------

from django.contrib.auth.decorators import login_required
from django.shortcuts import render


# @login_required = only logged-in users may open this page.
# Logged-out visitors are redirected to LOGIN_URL (the login page).
@login_required
def home(request):
    # Placeholder for the dashboard (built on Day 6).
    return render(request, 'tasks/home.html')
