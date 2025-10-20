# accounts/urls.py (Corrected)
# Add 'include' to the imports
from django.urls import path, include
from django.contrib.auth import views as auth_views
from .views import RegisterView

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    # Remove the login/logout paths we defined manually earlier
    # path('login/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
    # path('logout/', auth_views.LogoutView.as_view(), name='logout'),

    # Add this line to include all built-in auth URLs (login, logout, password reset, etc.)
    # They will automatically be prefixed with 'accounts/' because of config/urls.py
    path('', include('django.contrib.auth.urls')),
]