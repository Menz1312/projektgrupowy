(function() {
    // Pobieramy elementy
    const btn = document.getElementById('theme-toggle');
    const icon = document.getElementById('theme-icon');
    
    // Bezpieczna funkcja do obsługi localStorage (nie wysypie się w trybie prywatnym)
    function getStoredTheme() {
        try {
            return localStorage.getItem('theme');
        } catch (e) {
            return null;
        }
    }

    function setStoredTheme(theme) {
        try {
            localStorage.setItem('theme', theme);
        } catch (e) {}
    }

    // Główna funkcja ustawiająca motyw
    function setTheme(theme) {
        // 1. Ustaw atrybut dla CSS
        document.documentElement.setAttribute('data-theme', theme);
        
        // 2. Zapisz w pamięci przeglądarki
        setStoredTheme(theme);
        
        // 3. Podmień ikonę (jeśli istnieje)
        if (icon) {
            if (theme === 'dark') {
                // Jeśli ciemny -> pokaż Słońce (żeby przełączyć na jasny)
                icon.classList.remove('bi-moon-stars-fill');
                icon.classList.add('bi-sun-fill');
            } else {
                // Jeśli jasny -> pokaż Księżyc (żeby przełączyć na ciemny)
                icon.classList.remove('bi-sun-fill');
                icon.classList.add('bi-moon-stars-fill');
            }
        }
    }

    // --- INICJALIZACJA ---
    
    // Sprawdź czy użytkownik ma zapisany wybór
    const storedTheme = getStoredTheme();
    // Sprawdź czy system operacyjny jest w trybie ciemnym
    const systemDark = window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches;
    
    // Ustal motyw startowy (priorytet: zapisany > systemowy > domyślny jasny)
    const currentTheme = storedTheme || (systemDark ? 'dark' : 'light');
    
    // Uruchom ustawianie
    setTheme(currentTheme);

    // --- OBSŁUGA KLIKNIĘCIA ---
    if (btn) {
        btn.addEventListener('click', function() {
            // Pobierz aktualny motyw bezpośrednio z HTML-a
            const current = document.documentElement.getAttribute('data-theme');
            // Przełącz na przeciwny
            const newTheme = current === 'dark' ? 'light' : 'dark';
            setTheme(newTheme);
        });
    }
})();