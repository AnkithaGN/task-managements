# ---------------------------------------------------------------
# accounts/urls.py
# Addresses for registration, login and logout.
# Full addresses start with /accounts/ (see config/urls.py).
# ---------------------------------------------------------------

from django.contrib.auth import views as auth_views
from django.urls import path

from . import views
from .forms import EmailLoginForm

urlpatterns = [
    # /accounts/register/ -> our register view
    path('register/', views.register, name='register'),

    # /accounts/login/ -> Django's built-in LoginView, using our email form
    path(
        'login/',
        auth_views.LoginView.as_view(
            template_name='accounts/login.html',
            authentication_form=EmailLoginForm,
            redirect_authenticated_user=True,   # logged-in users skip the login page
        ),
        name='login',
    ),

    # /accounts/logout/ -> Django's built-in LogoutView (accepts POST only)
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
]