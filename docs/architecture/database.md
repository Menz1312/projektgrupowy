# Schemat Bazy Danych (ERD)

```mermaid
erDiagram
    %% Tabela Użytkowników (Custom User)
    User {
        int id PK
        string username
        string email
        string password
        bool is_staff
        bool is_active
        datetime date_joined
    }

    %% Aplikacja QUIZZES
    Quiz {
        int id PK
        string title
        string description
        string visibility "PUBLIC/PRIVATE"
        int time_limit "minuty"
        int questions_count_limit "limit pytań"
        bool instant_feedback
        datetime created_at
        int author_id FK
    }

    Question {
        int id PK
        string text
        string explanation
        string question_type "SINGLE/MULTIPLE"
        int quiz_id FK
    }

    Answer {
        int id PK
        string text
        bool is_correct
        int question_id FK
    }

    QuizGroup {
        int id PK
        string name
        string description
        int owner_id FK
    }

    QuizAttempt {
        int id PK
        int score
        int correct_count
        int total_questions
        bool time_over
        datetime completed_at
        int user_id FK
        int quiz_id FK
    }

    %% Tabele Uprawnień (Explicit Models)
    QuizUserPermission {
        int id PK
        string role "VIEWER/EDITOR"
        int user_id FK
        int quiz_id FK
    }

    QuizGroupPermission {
        int id PK
        string role "VIEWER/EDITOR"
        int group_id FK
        int quiz_id FK
    }

    %% RELACJE
    %% Jeden user ma wiele quizów (autor)
    User ||--o{ Quiz : "tworzy (author)"
    
    %% Jeden user ma wiele grup (właściciel)
    User ||--o{ QuizGroup : "posiada (owner)"
    
    %% Relacja Many-to-Many: Userzy należą do grup
    %% (W Django to tabela ukryta, tu pokazujemy logiczne połączenie)
    User }|--|{ QuizGroup : "należy do (members)"

    %% User ma wiele podejść do quizów
    User ||--o{ QuizAttempt : "rozwiązuje"

    %% Struktura Quizu
    Quiz ||--|{ Question : "zawiera"
    Question ||--|{ Answer : "posiada"
    
    %% Logika podejść
    Quiz ||--o{ QuizAttempt : "jest rozwiązywany"

    %% Uprawnienia
    Quiz ||--o{ QuizUserPermission : "ma uprawnienia użytkownika"
    User ||--o{ QuizUserPermission : "ma przypisane uprawnienie"
    
    Quiz ||--o{ QuizGroupPermission : "ma uprawnienia grupowe"
    QuizGroup ||--o{ QuizGroupPermission : "ma nadane uprawnienie"
```

## Opis Modeli Danych (Słownik Danych)

Poniższa tabela opisuje rolę poszczególnych encji w systemie oraz kluczowe decyzje projektowe.

| Model (Encja) | Aplikacja | Opis i Odpowiedzialność |
| :--- | :--- | :--- |
| **User** | `accounts` | Niestandardowy model użytkownika dziedziczący po `AbstractUser`. Pozwala na łatwą rozbudowę profilu w przyszłości bez naruszania struktury `auth_user`. |
| **Quiz** | `quizzes` | Centralna encja systemu. Przechowuje metadane quizu (tytuł, widoczność) oraz konfigurację rozgrywki (`time_limit`, `instant_feedback`). |
| **Question** | `quizzes` | Pojedyncze pytanie przypisane do quizu. Obsługuje różne typy pytań (jednokrotny/wielokrotny wybór) zdefiniowane w polu `question_type`. |
| **Answer** | `quizzes` | Odpowiedź do pytania. Zawiera flagę `is_correct`, która determinuje poprawność zaznaczenia. |
| **QuizGroup** | `quizzes` | Grupa użytkowników (np. "Klasa 3B"). Pozwala na masowe udostępnianie prywatnych quizów wielu osobom naraz. |
| **QuizAttempt** | `quizzes` | Historia wyników. Każdy rekord to jedno zakończone podejście do quizu, zawierające wynik punktowy, procentowy i czas wykonania. |

## Mechanizmy i Relacje

### 1. System Uprawnień (RBAC)
Zamiast polegać wyłącznie na prostych flagach, system wykorzystuje **tabele pośrednie** do zarządzania dostępem do prywatnych quizów. Pozwala to na elastyczne nadawanie ról:

* **QuizUserPermission**: Łączy bezpośrednio użytkownika z quizem, nadając mu rolę `VIEWER` (może rozwiązywać) lub `EDITOR` (może edytować).
* **QuizGroupPermission**: Łączy grupę użytkowników z quizem. Wszyscy członkowie grupy dziedziczą uprawnienia nadane grupie.

### 2. Logika Podejść (Attempts)
Model `QuizAttempt` jest tworzony w momencie zakończenia quizu.
* Wynik (`score`) jest obliczany po stronie serwera, aby zapobiec manipulacjom.
* Dla zachowania integralności danych historycznych, podejście jest powiązane z użytkownikiem relacją, która dopuszcza wartość `NULL` (w przypadku usunięcia konta użytkownika, jego statystyki pozostają w systemie jako anonimowe).

## Uwagi Techniczne

* **Silnik Bazy Danych:** Projekt domyślnie wykorzystuje **SQLite** (plik `db.sqlite3`) ze względu na łatwość konfiguracji w środowisku deweloperskim. W środowisku produkcyjnym zalecana jest migracja na **PostgreSQL**.
* **Migracje:** Wszelkie zmiany w strukturze bazy danych są wersjonowane przy użyciu systemu migracji Django (`python manage.py makemigrations` / `migrate`), co zapewnia spójność schematu między środowiskami.