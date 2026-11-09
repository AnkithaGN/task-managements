# ---------------------------------------------------------------
# accounts/backends.py
# Lets users log in with EMAIL + password instead of username.
# Django calls authenticate() below during login.
# ---------------------------------------------------------------

from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend

# The User model the project uses (Django's built-in auth_user).
User = get_user_model()


class EmailBackend(ModelBackend):
    """Authenticate a user by email address (case-insensitive) and password."""

    def authenticate(self, request, username=None, password=None, **kwargs):
        # Django's login form sends the typed value as "username".
        # On our login page that box will contain the EMAIL.
        email = kwargs.get('email', username)

        # Nothing typed: cannot be a valid login.
        if not email or not password:
            return None

        try:
            # email__iexact = exact match, ignoring upper/lower case.
            # So "Anki@Mail.com" and "anki@mail.com" find the same user.
            user = User.objects.get(email__iexact=email)
        except User.DoesNotExist:
            # No user with this email. Hash the password anyway so a wrong
            # email takes the same time as a wrong password (hides which
            # emails are registered from attackers).
            User().set_password(password)
            return None
        except User.MultipleObjectsReturned:
            # Two accounts share this email: refuse rather than guess.
            return None

        # check_password compares the hash, never plain text.
        # user_can_authenticate refuses deactivated accounts.
        if user.check_password(password) and self.user_can_authenticate(user):
            return user
        return None