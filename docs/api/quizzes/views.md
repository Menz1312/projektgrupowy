# Widoki Aplikacji Quizy

Dokumentacja logiki biznesowej zawartej w pliku `quizzes/views.py`. Widoki te obsługują żądania HTTP, renderują szablony HTML i zarządzają przepływem danych.

## Strona Główna i Pulpit

Widoki dostępne dla użytkowników w celu nawigacji i przeglądania dostępnych quizów.

::: quizzes.views.home_view
    options:
      show_root_heading: true

::: quizzes.views.my_quizzes_view
    options:
      show_root_heading: true

::: quizzes.views.quiz_detail_view
    options:
      show_root_heading: true

## Rozwiązywanie Quizu

Główna logika przeprowadzania testów i zapisywania wyników.

::: quizzes.views.quiz_take_view
    options:
      show_root_heading: true

## Zarządzanie Grupami Użytkowników

Widoki CRUD (Create, Read, Update, Delete) dla modelu `QuizGroup`.

::: quizzes.views.group_list_view
::: quizzes.views.group_create_view
::: quizzes.views.group_edit_view
::: quizzes.views.group_delete_view

## Zarządzanie Quizami (Nauczyciel/Autor)

Widoki pozwalające na tworzenie i edycję parametrów quizów.

::: quizzes.views.quiz_create_view
::: quizzes.views.quiz_edit_view
::: quizzes.views.quiz_delete_view

## Zarządzanie Pytaniami

Widoki obsługujące dodawanie, edycję i usuwanie pojedynczych pytań w ramach quizu.

::: quizzes.views.question_create_view
::: quizzes.views.question_edit_view
::: quizzes.views.question_delete_view

## Funkcje Specjalne

Zaawansowane funkcje takie jak generowanie quizów przez AI oraz Import/Eksport danych.

::: quizzes.views.quiz_generate_view
::: quizzes.views.quiz_export_json_view
::: quizzes.views.quiz_import_json_view