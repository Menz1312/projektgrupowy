# accounts/forms.py

from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from .models import User
from django import forms # Dodaj ten import

class CustomUserCreationForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('username', 'email')

# NOWA KLASA FORMULARZA DO EDYCJI PROFILU
class UserProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'email')
        labels = {
            'first_name': 'Imię',
            'last_name': 'Nazwisko',
            'email': 'Adres e-mail',
        }