# ---------------------------------------------------------------
# accounts/forms.py
# Forms for registration and email login.
# Forms validate user input ON THE SERVER before anything is saved.
# ---------------------------------------------------------------

from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm

User = get_user_model()


class RegisterForm(UserCreationForm):
    """Registration: username, email, password, password confirmation."""

    # Add an email field. Django's User has an email column,
    # but UserCreationForm does not ask for it, and it is optional by default.
    email = forms.EmailField(
        required=True,
        max_length=254,
        help_text='You will log in with this email.',
    )

    # Meta tells a ModelForm which model and fields to use.
    # We extend the parent's Meta and list the fields in display order.
    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('username', 'email')

    # clean_<fieldname>() = an extra check for one field.
    # Django calls it automatically during is_valid().
    def clean_email(self):
        # Normalise: remove spaces, store lowercase.
        email = self.cleaned_data['email'].strip().lower()

        # Refuse an email that is already registered (any upper/lower case).
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError('An account with this email already exists.')

        # Whatever we return becomes the cleaned value that gets saved.
        return email


class EmailLoginForm(AuthenticationForm):
    """Login form whose first box is an email address."""

    # AuthenticationForm calls its first field "username" and passes it to
    # authenticate(). Our EmailBackend treats that value as an email.
    username = forms.EmailField(
        label='Email',
        widget=forms.EmailInput(attrs={'autofocus': True}),
    )

    # Keep Django's other messages, replace only the wrong-login message.
    # The message does NOT say which part was wrong (safer).
    error_messages = {
        **AuthenticationForm.error_messages,
        'invalid_login': 'Incorrect email or password.',
    }