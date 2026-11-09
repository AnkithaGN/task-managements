# ---------------------------------------------------------------
# accounts/views.py
# Registration view. (Login and logout use Django's built-in views,
# configured in accounts/urls.py.)
# ---------------------------------------------------------------

from django.contrib import messages
from django.contrib.auth import login
from django.shortcuts import redirect, render

from .forms import RegisterForm


def register(request):
    # Already logged in? Registering again makes no sense: go home.
    if request.user.is_authenticated:
        return redirect('home')

    if request.method == 'POST':
        # The user submitted the form: fill it with what they typed.
        form = RegisterForm(request.POST)

        if form.is_valid():
            # Create the user in auth_user (password is stored as a HASH).
            user = form.save()

            # Log the new user in straight away.
            # backend= is required because we have 2 backends in settings.
            login(request, user, backend='accounts.backends.EmailBackend')

            # A one-time message shown on the next page.
            messages.success(request, f'Welcome, {user.username}! Your account was created.')

            # Redirect (Post/Redirect/Get): a page refresh will not re-submit the form.
            return redirect('home')
    else:
        # First visit (GET): an empty form.
        form = RegisterForm()

    # Show the page. If the form was invalid, it now contains the error messages.
    return render(request, 'accounts/register.html', {'form': form})
