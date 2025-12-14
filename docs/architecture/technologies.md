# Technologie i Biblioteki

W projekcie QuizApp wykorzystano nowoczesny stos technologiczny oparty na języku Python i frameworku Django, uzupełniony o lekkie rozwiązania frontendowe oraz integrację z usługami AI.

## Backend

### Język i Framework
* **Python 3.12+**: Główny język programowania logiki biznesowej.
* **Django 5.x**: Wysokopoziomowy framework webowy realizujący wzorzec MVT (Model-View-Template). Odpowiada za:
    * Mapowanie obiektowo-relacyjne (ORM).
    * Routing URL i widoki.
    * System uwierzytelniania i autoryzacji.
    * Zarządzanie formularzami i panel administracyjny.

### Kluczowe Biblioteki Python
* **`requests`**: Wykorzystywana do komunikacji HTTP z zewnętrznym API (Hugging Face Inference API) w celu generowania pytań do quizów.
* **`python-dotenv`**: Służy do zarządzania zmiennymi środowiskowymi (takimi jak klucze API czy `SECRET_KEY`) wczytywanymi z pliku `.env`.

### Baza Danych
* **SQLite 3**: Domyślna, lekka baza danych wykorzystywana w środowisku deweloperskim i testowym. Nie wymaga osobnego procesu serwerowego, co ułatwia przenoszenie projektu.

---

## Frontend

Warstwa prezentacji jest generowana przez silnik szablonów Django (Django Templates) i renderowana po stronie serwera (SSR).

### Struktura i Styl
* **HTML5 / CSS3**: Standardowe technologie webowe.
* **Bootstrap 5.3**: Framework CSS wykorzystywany do budowy responsywnego interfejsu (RWD), układu siatki (Grid) oraz gotowych komponentów UI (karty, modale, alerty, navbar).
* **Bootstrap Icons**: Zestaw ikon wektorowych SVG używanych w interfejsie.

### Skrypty
* **JavaScript (Vanilla JS)**:
    * Obsługa logiki przełączania motywu (Dark/Light Mode).
    * Obsługa bannera Cookies.
    * Interaktywne elementy quizu (np. minutnik, zaznaczanie odpowiedzi) w widoku `quiz_take.html`.

---

## Integracje Zewnętrzne (AI)

### Hugging Face Inference API
Projekt wykorzystuje model językowy (LLM) udostępniany przez Hugging Face (np. `meta-llama/Meta-Llama-3-8B-Instruct`) do automatycznego generowania pytań quizowych na podstawie tematu podanego przez użytkownika.

* **Endpoint**: `https://router.huggingface.co/v1/chat/completions`
* **Format danych**: JSON (wymiana promptów i sformatowanych pytań).