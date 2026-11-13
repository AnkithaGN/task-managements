# ---------------------------------------------------------------
# accounts/urls.py
# Addresses for registration, login, logout, profile and password change.
# Full addresses start with /accounts/ (see config/urls.py).
# ---------------------------------------------------------------

from django.contrib.auth import views as auth_views
from django.urls import path, reverse_lazy

from . import views
from .forms import EmailLoginForm

urlpatterns = [
    path('register/', views.register, name='register'),
    path(
        'login/',
        auth_views.LoginView.as_view(
            template_name='accounts/login.html',
            authentication_form=EmailLoginForm,
            redirect_authenticated_user=True,   # logged-in users skip the login page
        ),
        name='login',
    ),
    # LogoutView accepts POST only (protects against forced logout).
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),

    # Profile: no id in the address -> always the logged-in user.
    path('profile/', views.profile, name='profile'),
    path('profile/edit/', views.profile_edit, name='profile_edit'),

    # Password change: Django's built-in, secure views.
    # They require login, check the OLD password, apply the password rules,
    # store the new password as a hash, and keep the user logged in.
    path(
        'password/',
        auth_views.PasswordChangeView.as_view(
            template_name='accounts/password_change.html',
            success_url=reverse_lazy('password_change_done'),
        ),
        name='password_change',
    ),
    path(
        'password/done/',
        auth_views.PasswordChangeDoneView.as_view(
            template_name='accounts/password_change_done.html',
        ),
        name='password_change_done',
    ),
]
