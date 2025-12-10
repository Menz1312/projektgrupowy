from django.contrib.auth.models import AbstractUser, Group, Permission
from django.db import models

class User(AbstractUser):
    """
    Niestandardowy model użytkownika aplikacji.

    Rozszerza standardowy model Django `AbstractUser`, co pozwala na łatwiejsze
    dodawanie własnych pól w przyszłości oraz pełną kontrolę nad procesem uwierzytelniania.
    
    W tym projekcie model ten jest wykorzystywany jako `AUTH_USER_MODEL` w ustawieniach.

    Attributes:
        groups (ManyToManyField): Grupy, do których należy użytkownik. 
            Nadpisane pole systemowe w celu uniknięcia konfliktów nazw relacji zwrotnych (`related_name`).
        user_permissions (ManyToManyField): Specyficzne uprawnienia przypisane bezpośrednio do użytkownika.
            Nadpisane pole systemowe w celu uniknięcia konfliktów nazw relacji zwrotnych.
    """
    
    # Nadpisujemy pola groups i user_permissions, aby rozwiązać potencjalne konflikty
    # nazw (related_name clash) w przypadku, gdyby w projekcie istniały odwołania
    # do domyślnego auth.User.
    
    groups = models.ManyToManyField(
        Group,
        verbose_name='groups',
        blank=True,
        help_text=(
            'Grupy, do których należy ten użytkownik. Użytkownik otrzyma wszystkie '
            'uprawnienia przyznane każdej z jego grup.'
        ),
        related_name="%(app_label)s_%(class)s_groups",
        related_query_name="user",
    )
    
    user_permissions = models.ManyToManyField(
        Permission,
        verbose_name='user permissions',
        blank=True,
        help_text='Specyficzne uprawnienia dla tego użytkownika.',
        related_name="%(app_label)s_%(class)s_user_permissions",
        related_query_name="user",
    )