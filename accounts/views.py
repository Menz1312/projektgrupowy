from django.urls import reverse_lazy
from django.views.generic import CreateView
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse, HttpRequest
from .forms import CustomUserCreationForm, UserProfileForm

class RegisterView(CreateView):
    """
    Widok rejestracji nowego użytkownika.

    Wykorzystuje wbudowany w Django generyczny widok `CreateView` do obsługi
    procesu tworzenia konta. Po pomyślnej rejestracji przekierowuje do strony logowania.

    Attributes:
        form_class (Form): Klasa formularza używana do rejestracji (`CustomUserCreationForm`).
        success_url (str): URL przekierowania po udanej rejestracji (`login`).
        template_name (str): Ścieżka do szablonu HTML (`registration/register.html`).
    """
    form_class = CustomUserCreationForm
    success_url = reverse_lazy('login')
    template_name = 'registration/register.html'

@login_required
def profile_edit_view(request: HttpRequest) -> HttpResponse:
    """
    Widok edycji profilu zalogowanego użytkownika.

    Pozwala użytkownikowi zmienić swoje dane (imię, nazwisko, email).
    Wymaga zalogowania (`@login_required`).

    **Obsługa żądań:**

    * **GET**: Wyświetla formularz wypełniony aktualnymi danymi użytkownika.
    * **POST**: Waliduje i zapisuje zmiany. W przypadku sukcesu wyświetla komunikat
        i przeładowuje stronę (wzorzec PRG - Post/Redirect/Get).

    Args:
        request (HttpRequest): Obiekt żądania HTTP zawierający dane użytkownika (`request.user`).

    Returns:
        HttpResponse: Wyrenderowany szablon `registration/profile_edit.html` z formularzem.
    """
    if request.method == 'POST':
        form = UserProfileForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Twój profil został zaktualizowany!')
            return redirect('profile_edit') # Przekieruj z powrotem na tę samą stronę
    else:
        form = UserProfileForm(instance=request.user) # Wypełnij formularz danymi użytkownika

    return render(request, 'registration/profile_edit.html', {'form': form})