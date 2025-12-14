# Modele Aplikacji Quizy

Dokumentacja struktur danych zdefiniowanych w `quizzes/models.py`. Modele te odpowiadają za przechowywanie quizów, pytań, odpowiedzi, a także zarządzanie dostępem i wynikami.

## Główna Struktura Quizu

Modele tworzące rdzeń funkcjonalności quizów.

::: quizzes.models.Quiz
    options:
      show_root_heading: true
      members: false

::: quizzes.models.Question
    options:
      show_root_heading: true
      members: false

::: quizzes.models.Answer
    options:
      show_root_heading: true
      members: false

## Uprawnienia i Grupy

Modele odpowiedzialne za system udostępniania quizów użytkownikom i grupom.

::: quizzes.models.QuizGroup
    options:
      show_root_heading: true
      members: false

::: quizzes.models.QuizUserPermission
    options:
      show_root_heading: true
      heading_level: 3
      members: false

::: quizzes.models.QuizGroupPermission
    options:
      show_root_heading: true
      heading_level: 3
      members: false

## Wyniki i Analityka

Modele przechowujące historię rozwiązywania quizów.

::: quizzes.models.QuizAttempt
    options:
      show_root_heading: true
      members: false