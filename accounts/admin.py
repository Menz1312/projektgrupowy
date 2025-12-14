# accounts/admin.py
"""
Moduł konfiguracji panelu administracyjnego dla aplikacji accounts.

Rejestruje niestandardowy model użytkownika oraz dostosowuje jego widok
w panelu admina Django.
"""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User
from .forms import CustomUserCreationForm

class CustomUserAdmin(UserAdmin):
    """
    Niestandardowa konfiguracja panelu admina dla modelu User.

    Rozszerza domyślny `UserAdmin`, aby korzystał z niestandardowego formularza
    tworzenia użytkownika oraz definiuje, jakie pola są wyświetlane na liście.

    Attributes:
        add_form (Form): Formularz używany do tworzenia nowych użytkowników (`CustomUserCreationForm`).
        model (Model): Model, którym zarządza ta klasa (`User`).
        list_display (list): Pola wyświetlane w kolumnach na liście użytkowników.
        list_filter (list): Pola, po których można filtrować listę (prawy pasek boczny).
        search_fields (list): Pola przeszukiwane przez pasek wyszukiwania.
    """
    # Używamy niestandardowego formularza do tworzenia użytkownika (zgodnie z accounts/forms.py)
    add_form = CustomUserCreationForm 
    
    # Model, którym zarządzamy
    model = User
    
    # Pola widoczne na liście użytkowników
    list_display = ['username', 'email', 'first_name', 'last_name', 'is_staff', 'is_active']
    
    # Filtry dostępne po prawej stronie listy
    list_filter = ['is_staff', 'is_active', 'is_superuser']
    
    # Wyszukiwarka - przeszukuje te pola
    search_fields = ['username', 'email', 'first_name', 'last_name']
    
    # Domyślne fieldsets z UserAdmin zawierają już sekcje do zarządzania
    # uprawnieniami (is_staff, is_superuser, groups, user_permissions),
    # więc nie musimy ich ręcznie dodawać.

# Rejestrujemy model User w panelu admina z naszą konfiguracją
admin.site.register(User, CustomUserAdmin)