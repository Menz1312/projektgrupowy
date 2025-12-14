# quizzes/apps.py
"""
Konfiguracja aplikacji quizzes.
"""

from django.apps import AppConfig


class QuizzesConfig(AppConfig):
    """
    Klasa konfiguracyjna dla głównej aplikacji quizów.

    Attributes:
        default_auto_field (str): Typ pola klucza głównego.
        name (str): Nazwa aplikacji.
    """
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'quizzes'