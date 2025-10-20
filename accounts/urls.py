# accounts/urls.py

from django.urls import path, include # Upewnij się, że 'include' jest zaimportowane
from .views import RegisterView

urlpatterns = [
    # Ścieżka do widoku rejestracji
    path('register/', RegisterView.as_view(), name='register'),

    # Dołączenie wszystkich wbudowanych URLi Django dla uwierzytelniania
    # To automatycznie doda ścieżki takie jak:
    # login/, logout/, password_change/, password_reset/ itd.
    # Wszystkie będą poprzedzone prefiksem 'accounts/' z pliku config/urls.py
    path('', include('django.contrib.auth.urls')),
]