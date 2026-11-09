# ---------------------------------------------------------------
# config/urls.py
# The project's main URL list. It sends each address to an app.
# ---------------------------------------------------------------

from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path('admin/', admin.site.urls),             # Django Admin
    path('accounts/', include('accounts.urls')), # register, login, logout
    path('', include('tasks.urls')),             # everything else: tasks
]