# ---------------------------------------------------------------
# accounts/views.py
# Registration and profile pages. (Login and logout use Django's
# built-in views, configured in accounts/urls.py.)
# ---------------------------------------------------------------

from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from .forms import ProfileForm, RegisterForm


def register(request):
    # Already logged in? Registering again makes no sense: go home.
    if request.user.is_authenticated:
        return redirect('home')

    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            # Create the user (password is stored as a HASH).
            user = form.save()
            # Log in straight away. backend= is required because we have 2 backends.
            login(request, user, backend='accounts.backends.EmailBackend')
            messages.success(request, f'Welcome, {user.username}! Your account was created.')
            # Post/Redirect/Get: a page refresh will not re-submit the form.
            return redirect('home')
    else:
        form = RegisterForm()

    return render(request, 'accounts/register.html', {'form': form})


@login_required
def profile(request):
    # Always the LOGGED-IN user: there is no way to view someone else's profile.
    return render(request, 'accounts/profile.html')


@login_required
def profile_edit(request):
    if request.method == 'POST':
        # instance=request.user -> update the logged-in user, never anyone else.
        form = ProfileForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Your profile was updated.')
            return redirect('profile')
    else:
        form = ProfileForm(instance=request.user)

    return render(request, 'accounts/profile_form.html', {'form': form})
