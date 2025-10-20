# config/urls.py (Corrected)
from django.contrib import admin
from django.urls import path, include
from django.views.generic.base import TemplateView

urlpatterns = [
    path('admin/', admin.site.urls),
    # Keep only the include for your accounts app
    path('accounts/', include('accounts.urls')),
    # REMOVE: path('accounts/', include('django.contrib.auth.urls')),
    path('', TemplateView.as_view(template_name='home.html'), name='home'),
]