# ---------------------------------------------------------------
# tasks/urls.py
# Addresses for the tasks app.
# ---------------------------------------------------------------

from django.urls import path

from . import views

urlpatterns = [
    # The site's main page "/" -> home (future dashboard)
    path('', views.home, name='home'),
]