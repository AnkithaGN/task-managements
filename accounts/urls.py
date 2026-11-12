# ---------------------------------------------------------------
# accounts/urls.py
# Addresses for registration, login, logout and profile.
# Full addresses start with /accounts/ (see config/urls.py).
# ---------------------------------------------------------------

from django.contrib.auth import views as auth_views
from django.urls import path

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
]