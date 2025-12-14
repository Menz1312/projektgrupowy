# accounts/forms.py
"""
Formularze dla aplikacji accounts.

Zawiera definicje formularzy używanych do rejestracji użytkowników oraz
edycji ich profili.
"""

from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from .models import User
from django import forms 

class CustomUserCreationForm(UserCreationForm):
    """
    Formularz rejestracji nowego użytkownika.

    Rozszerza wbudowany w Django `UserCreationForm` o obsługę niestandardowego
    modelu `User` oraz dodatkowe pola (np. email).

    Attributes:
        Meta: Klasa wewnętrzna definiująca metadane formularza.
    """
    class Meta(UserCreationForm.Meta):
        """
        Metadane formularza rejestracji.

        Attributes:
            model (Model): Model powiązany z formularzem (`User`).
            fields (tuple): Pola modelu, które mają znaleźć się w formularzu.
        """
        model = User
        fields = ('username', 'email')

# NOWA KLASA FORMULARZA DO EDYCJI PROFILU
class UserProfileForm(forms.ModelForm):
    """
    Formularz edycji profilu użytkownika.

    Pozwala zalogowanemu użytkownikowi na zmianę podstawowych danych osobowych
    takich jak imię, nazwisko i adres e-mail.

    Attributes:
        Meta: Klasa wewnętrzna definiująca metadane formularza.
    """
    class Meta:
        """
        Metadane formularza edycji profilu.

        Attributes:
            model (Model): Model powiązany z formularzem (`User`).
            fields (tuple): Pola modelu do edycji.
            labels (dict): Niestandardowe etykiety dla pól formularza.
        """
        model = User
        fields = ('first_name', 'last_name', 'email')
        labels = {
            'first_name': 'Imię',
            'last_name': 'Nazwisko',
            'email': 'Adres e-mail',
        }