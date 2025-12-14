# accounts/apps.py
"""
Konfiguracja aplikacji accounts.
"""

from django.apps import AppConfig


class AccountsConfig(AppConfig):
    """
    Klasa konfiguracyjna dla aplikacji zarządzającej kontami użytkowników.

    Attributes:
        default_auto_field (str): Typ pola klucza głównego dla modeli w tej aplikacji.
        name (str): Nazwa aplikacji w projekcie Django.
    """
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'accounts'