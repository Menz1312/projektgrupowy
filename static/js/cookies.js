document.addEventListener("DOMContentLoaded", function() {
    const banner = document.getElementById("cookie-banner");
    const acceptBtn = document.getElementById("accept-cookies");

    // Klucz w pamięci przeglądarki
    const storageKey = "quizapp_cookies_accepted";

    // Sprawdź, czy użytkownik już zaakceptował
    if (!localStorage.getItem(storageKey)) {
        // Jeśli nie, pokaż baner z małym opóźnieniem dla lepszego efektu
        setTimeout(() => {
            banner.classList.add("show");
        }, 500);
    }

    if (acceptBtn) {
        acceptBtn.addEventListener("click", function() {
            // Zapisz zgodę w pamięci
            localStorage.setItem(storageKey, "true");
            // Ukryj baner
            banner.classList.remove("show");
        });
    }
});