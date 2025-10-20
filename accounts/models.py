# accounts/models.py
from django.contrib.auth.models import AbstractUser, Group, Permission # Import Group and Permission
from django.db import models # Import models

class User(AbstractUser):
    # Add these two fields to resolve the clashes
    groups = models.ManyToManyField(
        Group,
        verbose_name='groups',
        blank=True,
        help_text=(
            'The groups this user belongs to. A user will get all permissions '
            'granted to each of their groups.'
        ),
        # Use related_name like 'custom_user_groups' or the app/class pattern
        related_name="%(app_label)s_%(class)s_groups",
        related_query_name="user",
    )
    user_permissions = models.ManyToManyField(
        Permission,
        verbose_name='user permissions',
        blank=True,
        help_text='Specific permissions for this user.',
        # Use related_name like 'custom_user_permissions' or the app/class pattern
        related_name="%(app_label)s_%(class)s_user_permissions",
        related_query_name="user",
    )
    # You can add other custom fields here later if needed
    pass # Keep pass if you have no other custom fields yet