# Frontend i Zasoby Statyczne

Warstwa prezentacji aplikacji QuizApp oparta jest na silniku szablonów Django (DTL) wspieranym przez framework CSS Bootstrap 5. Aplikacja wykorzystuje hybrydowe podejście do zarządzania zasobami: biblioteki zewnętrzne ładowane są z sieci CDN, a style i skrypty specyficzne dla projektu znajdują się w katalogu lokalnym.

## 📂 Struktura Katalogów

Zasoby frontendowe są podzielone na dwa główne katalogi: `static` (pliki serwowane bezpośrednio) oraz `templates` (pliki HTML renderowane przez Django).

```text
projektgrupowy/
├── static/                 # Pliki statyczne (CSS, JS, Obrazy)
│   ├── css/
│   │   └── style.css       # Główne style globalne i zmienne CSS
│   └── js/
│       ├── cookies.js      # Obsługa bannera plików cookies
│       └── theme.js        # Logika przełączania motywu (Dark/Light)
└── templates/              # Szablony Django (HTML)
    ├── base.html           # Główny layout (szkielet strony)
    ├── home.html           # Strona główna
    ├── quizzes/            # Szablony aplikacji Quizy
    └── registration/       # Szablony logowania i rejestracji
```

---

## 🎨 Style i Motywy (CSS)

Głównym arkuszem stylów jest plik `static/css/style.css`. Projekt wykorzystuje natywne zmienne CSS (CSS Variables) do obsługi dynamicznej zmiany motywu (Jasny/Ciemny).

### Zmienne Kolorystyczne
Kolory są definiowane semantycznie w pseudoklasie `:root` oraz nadpisywane dla atrybutu `[data-bs-theme="dark"]`.

```css
/* Definicja w style.css */
:root {
    --primary-color: #4f46e5;
    --secondary-color: #ec4899;
    --background-color: #f8f9fa;
    --card-bg: #ffffff;
    --text-color: #212529;
}

[data-bs-theme="dark"] {
    --background-color: #212529;
    --card-bg: #2c3035;
    --text-color: #f8f9fa;
}
```

### Framework Bootstrap 5.3
Projekt korzysta z Bootstrapa ładowanego z CDN (JSDelivr) w pliku `base.html`.
* **Wersja:** 5.3.3
* **Ikony:** Bootstrap Icons 1.11.3
* **Komponenty:** Navbar, Cards, Modals, Alerts, Forms.

---

## 📜 Skrypty JavaScript

Logika po stronie klienta (Client-side) została ograniczona do niezbędnego minimum, aby zapewnić szybkość działania i interaktywność interfejsu.

### `theme.js` (Tryb Ciemny)
Odpowiada za obsługę przełącznika motywów w nawigacji.

1. Sprawdza ustawienie w `localStorage` przeglądarki.
2. Jeśli brak ustawienia, sprawdza preferencje systemowe (`prefers-color-scheme`).
3. Ustawia atrybut `data-bs-theme` na elemencie `<html>`.
4. Nasłuchuje kliknięcia w ikonę przełącznika i zapisuje wybór użytkownika.

### `cookies.js` (Polityka Prywatności)
Prosty skrypt zarządzający wyświetlaniem bannera informacyjnego o plikach cookies.
* **Mechanizm:** Sprawdza obecność klucza `cookiesAccepted` w `localStorage`. Jeśli go nie ma, wyświetla modal/banner na dole strony.

---

## 🧩 Szablony (Templates)

System szablonów oparty jest na **dziedziczeniu**. Główny plik `base.html` definiuje szkielet strony HTML5, a pozostałe szablony jedynie wypełniają zdefiniowane w nim bloki.

### Hierarchia Szablonów

```mermaid
graph TD
    Base[base.html<br/>(Szkielet, Navbar, Footer)]
    
    Base --> Home[home.html]
    Base --> Auth[registration/...]
    Base --> QuizBase[quizzes/...]
    
    subgraph "Przykładowe Widoki"
    Auth --> Login[login.html]
    Auth --> Register[register.html]
    QuizBase --> QuizList[my_quizzes.html]
    QuizBase --> QuizDetail[quiz_detail.html]
    QuizBase --> QuizTake[quiz_take.html]
    end

    style Base fill:#f9f,stroke:#333,stroke-width:2px
```

### Kluczowe bloki w `base.html`:
{% raw %}
* `{% block title %}`: Tytuł strony (SEO).
* `{% block content %}`: Główna zawartość podstrony.
* `{% block scripts %}`: Miejsce na dołączenie skryptów specyficznych dla danej podstrony (np. timer w quizie).
{% endraw %}

!!! info "Komunikaty Django (Messages)"
    Plik `base.html` zawiera wbudowaną pętlę obsługującą `django.contrib.messages`. Komunikaty (sukcesu, błędu, info) są automatycznie renderowane jako alerty Bootstrapa nad główną zawartością strony.