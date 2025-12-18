# Formularze Aplikacji Quizy

Dokumentacja formularzy Django (`django.forms`) zdefiniowanych w `quizzes/forms.py`. Formularze te obsługują walidację danych wejściowych, generowanie HTML oraz logikę zapisu danych.

## Konfiguracja Quizu

Formularze używane w widokach `QuizCreateView` oraz `QuizEditView`.

::: quizzes.forms.QuizForm
    options:
      show_root_heading: true
      members: false

### Formsety Uprawnień

Formsety (zestawy formularzy) służące do zarządzania relacjami Many-To-Many dla uprawnień w jednym widoku edycji quizu.

::: quizzes.forms.QuizUserPermissionFormSet
    options:
      show_root_heading: true
      show_source: false
      members: false

::: quizzes.forms.QuizGroupPermissionFormSet
    options:
      show_root_heading: true
      show_source: false
      members: false

## Zarządzanie Pytaniami

Formularze używane w widoku edycji i tworzenia pytań (`QuestionCreateView`, `QuestionEditView`).

::: quizzes.forms.QuestionForm
    options:
      show_root_heading: true
      members: false

## Zarządzanie Grupami

::: quizzes.forms.QuizGroupForm
    options:
      show_root_heading: true
      members: false

## Narzędzia Dodatkowe

::: quizzes.forms.QuizGenerationForm
    options:
      show_root_heading: true
      members: false