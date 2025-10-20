# config/urls.py

from django.contrib import admin
from django.urls import path, include
from django.views.generic.base import TemplateView # Potrzebne dla strony głównej

urlpatterns = [
    path('admin/', admin.site.urls),

    # Wszystkie adresy zaczynające się od 'accounts/' będą szukane w pliku accounts/urls.py
    path('accounts/', include('accounts.urls')),

    # Prosta strona główna (wymaga pliku templates/home.html)
    path('', TemplateView.as_view(template_name='home.html'), name='home'),
]