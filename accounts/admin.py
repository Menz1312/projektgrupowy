# accounts/admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User
from .forms import CustomUserCreationForm

# Rozszerzamy domyślny UserAdmin, aby korzystał z naszego modelu User
class CustomUserAdmin(UserAdmin):
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