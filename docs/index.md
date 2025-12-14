# Witaj w dokumentacji QuizApp 👋

**QuizApp** to interaktywna platforma edukacyjna stworzona w ramach projektu zespołowego na Wydziale Informatyki i Sztucznej Inteligencji Politechniki Częstochowskiej. Aplikacja umożliwia tworzenie, udostępnianie oraz rozwiązywanie testów wiedzy, wykorzystując nowoczesne technologie webowe oraz wsparcie sztucznej inteligencji.

---

## 🚀 Główne Funkcjonalności

Aplikacja oferuje szereg narzędzi zarówno dla twórców quizów, jak i użytkowników rozwiązujących:

* **Zarządzanie Quizami**: Pełny system CRUD do tworzenia quizów z pytaniami jednokrotnego i wielokrotnego wyboru.
* **Generator AI 🤖**: Unikalna funkcja automatycznego generowania pytań na dowolny temat przy użyciu modelu językowego (integracja z Hugging Face API).
* **Grupy Użytkowników**: System uprawnień pozwalający na tworzenie grup (np. klas) i udostępnianie im prywatnych quizów.
* **Zaawansowany Tryb Rozwiązywania**: Obsługa limitów czasowych, losowania puli pytań oraz opcjonalny tryb "natychmiastowej odpowiedzi" (instant feedback).
* **Konta Użytkowników**: System rejestracji, logowania oraz śledzenia historii wyników (podejść do quizów).

---

## 📚 Przewodnik po Dokumentacji

Dokumentacja techniczna została podzielona na sekcje odzwierciedlające architekturę projektu:

### 1. [Architektura Systemu](architecture/structure.md)
Fundamenty techniczne projektu. W tej sekcji znajdziesz:
* **Strukturę projektu** (drzewo plików).
* Opis zastosowanych **technologii i bibliotek** (Stack technologiczny).
* Diagram i schemat **bazy danych (ERD)**.

### 2. Dokumentacja API (Reference)
Szczegółowy opis kodu źródłowego, wygenerowany automatycznie na podstawie docstringów:
* **Aplikacja Quizy**: [Modele](api/quizzes/models.md), [Logika Widoków](api/quizzes/views.md), [Formularze](api/quizzes/forms.md).
* **Aplikacja Użytkownicy**: [Modele](api/accounts/models.md) i [Widoki](api/accounts/views.md).

### 3. [Frontend](frontend/assets.md)
Informacje dotyczące warstwy prezentacji, stylów CSS oraz skryptów JavaScript.

---

## ℹ️ Informacje Dodatkowe

!!! info "Wdrożenie i Instalacja"
    Pełna instrukcja instalacji, konfiguracji środowiska (`.env`) oraz procedury wdrożeniowej znajduje się w zewnętrznej dokumentacji projektu na platformie **Confluence**.

Projekt jest rozwijany w języku **Python** z wykorzystaniem frameworka **Django**.