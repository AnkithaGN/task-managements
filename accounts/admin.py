# ---------------------------------------------------------------
# accounts/admin.py
# Shows user profiles (profile pictures) in Django Admin.
# ---------------------------------------------------------------

from django.contrib import admin

from .models import Profile


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'avatar']
    search_fields = ['user__username', 'user__email']
