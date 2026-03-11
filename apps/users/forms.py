"""Forms for user management."""
from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from django.utils.translation import gettext_lazy as _

from .models import User


class CustomUserCreationForm(UserCreationForm):
    """Custom form for user registration."""
    email = forms.EmailField(
        label=_('Email'),
        required=True,
        widget=forms.EmailInput(attrs={'class': 'form-control'})
    )
    phone_number = forms.CharField(
        label=_('Phone number'),
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('email', 'username', 'phone_number', 'password1', 'password2')


class CustomUserChangeForm(UserChangeForm):
    """Custom form for user profile editing."""
    class Meta(UserChangeForm.Meta):
        model = User
        fields = ('email', 'username', 'first_name', 'last_name', 'phone_number',
                 'avatar', 'date_of_birth', 'gender', 'language_preference')
        widgets = {
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control'}),
            'date_of_birth': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'gender': forms.Select(attrs={'class': 'form-control'}),
            'language_preference': forms.Select(attrs={'class': 'form-control'}),
        }