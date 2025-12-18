# Struktura Projektu

Projekt **QuizApp** został zorganizowany zgodnie ze standardową architekturą frameworka Django, z wyraźnym podziałem na aplikacje realizujące konkretne domeny biznesowe (użytkownicy, quizy) oraz konfigurację globalną.

## Drzewo Katalogów

Poniżej znajduje się aktualna struktura plików wygenerowana automatycznie z repozytorium:

{{ project_tree() }}

---

## Opis Kluczowych Modułów

### Główne Aplikacje

Projekt składa się z dwóch głównych aplikacji Django (Apps), co zapewnia separację odpowiedzialności:

| Katalog | Rola w systemie |
| :--- | :--- |
| **`accounts/`** | **Zarządzanie Użytkownikami.** <br> Odpowiada za rejestrację, logowanie, wylogowywanie oraz edycję profilu. Zawiera niestandardowy model użytkownika (`User`) rozszerzający `AbstractUser`. |
| **`quizzes/`** | **Logika Biznesowa (Core).** <br> Serce aplikacji. Zawiera modele Quizów, Pytań, Odpowiedzi oraz mechanizmy generowania quizów przez AI i zliczania wyników (QuizAttempt). |

### Konfiguracja i Narzędzia

| Katalog/Plik | Opis |
| :--- | :--- |
| **`config/`** | **Centrum sterowania.** Zawiera plik `settings.py` (ustawienia globalne), `urls.py` (główny routing) oraz konfigurację serwera WSGI/ASGI. |
| **`templates/`** | **Warstwa Prezentacji.** Globalny katalog szablonów HTML. Wewnątrz znajdują się podkatalogi dla poszczególnych aplikacji oraz plik `base.html` (główny layout). |
| **`static/`** | **Pliki Statyczne.** Przechowuje pliki CSS, JavaScript (np. obsługa motywów, cookies) oraz obrazy, które nie są wgrywane przez użytkowników. |
| **`manage.py`** | Skrypt narzędziowy Django do zarządzania projektem (uruchamianie serwera, tworzenie migracji). |
| **`mkdocs.yml`** | Konfiguracja niniejszej dokumentacji technicznej. |

## Konwencje

* **Szablony (Templates):** Projekt wykorzystuje jeden główny folder `templates/` w katalogu głównym (zamiast folderów wewnątrz każdej aplikacji), co ułatwia zarządzanie globalnym stylem.
* **Pliki statyczne:** Pliki CSS i JS są podzielone na podkatalogi `css/` i `js/` wewnątrz folderu `static/`.