# ---------------------------------------------------------------
# accounts/models.py
# Extra information about a user that Django's built-in User table
# does not have: the profile picture.
# ---------------------------------------------------------------

import uuid
from pathlib import Path

from django.conf import settings
from django.db import models


def avatar_upload_path(instance, filename):
    """Where an uploaded picture is saved, e.g. media/avatars/user_5/3f2a....png

    A random name (uuid4) is used instead of the user's file name, so names never
    clash and nobody can guess another user's file name.
    """
    extension = Path(filename).suffix.lower()
    return f'avatars/user_{instance.user_id}/{uuid.uuid4().hex}{extension}'


class Profile(models.Model):
    # One profile per user. OneToOneField = a ForeignKey that must be unique.
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,     # deleting the user deletes the profile
        related_name='profile',       # user.profile
    )
    # ImageField = a file field that only accepts real images (checked with Pillow).
    # The FILE is stored on disk (MEDIA_ROOT); the database only stores its path.
    avatar = models.ImageField(upload_to=avatar_upload_path, blank=True)

    def __str__(self):
        return f'Profile of {self.user}'


def get_profile(user):
    """Return the user's profile, creating an empty one the first time."""
    profile, _created = Profile.objects.get_or_create(user=user)
    return profile
