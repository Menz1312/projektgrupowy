projektgrupowy/
├── accounts/               # Uwierzytelnianie i profil użytkownika
│   ├── migrations/
│   ├── forms.py
│   ├── models.py
│   ├── urls.py
│   └── views.py
├── config/                 # Konfiguracja projektu Django
│   ├── settings.py         
│   ├── urls.py             
│   └── wsgi.py
├── quizzes/                # Aplikacja główna (Modele, Logika, Uprawnienia)
│   ├── migrations/
│   ├── admin.py
│   ├── forms.py            # Formularze dla quizów i grup
│   ├── models.py           # Modele Quiz, Question, Answer, Permissions, Attempt
│   ├── urls.py
│   └── views.py            # Logika (AI Generator, Rozwiązywanie, CRUD)
├── static/                 # Statyczne pliki (CSS, JS, motywy)
│   ├── css/
│   └── js/
├── templates/              # Główne szablony HTML
│   ├── base.html
│   └── ...
├── .gitignore
└── manage.py