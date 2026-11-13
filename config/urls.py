# ---------------------------------------------------------------
# config/urls.py
# The project's main URL list. It sends each address to an app.
# ---------------------------------------------------------------

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path('admin/', admin.site.urls),             # Django Admin
    path('accounts/', include('accounts.urls')), # register, login, logout, profile
    path('', include('tasks.urls')),             # everything else: tasks
]

# During development (DEBUG=True) Django itself serves uploaded files (profile pictures).
# On the real server (DEBUG=False) Nginx serves /media/ instead, which is faster and safer.
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
