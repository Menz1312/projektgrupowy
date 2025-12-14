# Widoki Użytkowników

Dokumentacja widoków aplikacji `accounts`, obsługujących procesy rejestracji oraz zarządzania profilem użytkownika. Pozostałe widoki uwierzytelniania (Logowanie, Wylogowanie, Reset hasła) są obsługiwane przez wbudowane widoki Django (`django.contrib.auth.views`).

## Rejestracja

::: accounts.views.RegisterView
    options:
      show_root_heading: true
      members: false

## Profil Użytkownika

::: accounts.views.profile_edit_view
    options:
      show_root_heading: true