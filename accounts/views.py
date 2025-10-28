# accounts/views.py

from django.urls import reverse_lazy
from django.views.generic import CreateView
from django.shortcuts import render, redirect # Dodaj importy
from django.contrib.auth.decorators import login_required # Dodaj import
from django.contrib import messages # Dodaj import
from .forms import CustomUserCreationForm, UserProfileForm # Dodaj import UserProfileForm

class RegisterView(CreateView):
    form_class = CustomUserCreationForm
    success_url = reverse_lazy('login')
    template_name = 'registration/register.html'

# NOWY WIDOK DO EDYCJI PROFILU
@login_required # Wymaga zalogowania
def profile_edit_view(request):
    if request.method == 'POST':
        form = UserProfileForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Twój profil został zaktualizowany!')
            return redirect('profile_edit') # Przekieruj z powrotem na tę samą stronę
    else:
        form = UserProfileForm(instance=request.user) # Wypełnij formularz danymi użytkownika

    return render(request, 'registration/profile_edit.html', {'form': form})