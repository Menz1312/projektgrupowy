# quizzes/tests.py
"""
Zestaw testów jednostkowych i integracyjnych dla aplikacji quizzes i accounts.

Zawiera testy sprawdzające logikę importu JSON, procesu rozwiązywania quizów,
tworzenia pytań oraz podstawowe funkcje kont użytkowników.
"""

import json
from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from .models import Quiz, Question, Answer, QuizUserPermission

# Pobieramy model użytkownika zdefiniowany w settings.py
User = get_user_model()


class QuizImportTests(TestCase):
    """
    Testy funkcjonalności importu quizów z plików JSON.
    """
    
    def setUp(self):
        """
        Przygotowuje środowisko testowe przed każdym testem.
        
        Tworzy użytkownika (autora), pusty quiz oraz definiuje adresy URL.
        """
        # 1. Stwórz użytkownika, który będzie autorem quizu
        self.user = User.objects.create_user(
            username='testauthor', 
            password='testpassword123'
        )
        
        # 2. Stwórz quiz należący do tego użytkownika
        self.quiz = Quiz.objects.create(
            title="Mój Quiz do Importu", 
            author=self.user,
            visibility='PRIVATE'
        )
        
        # 3. Zdefiniuj potrzebne adresy URL
        self.import_url = reverse('quiz-import-json', kwargs={'pk': self.quiz.pk})
        self.edit_url = reverse('quiz-edit', kwargs={'pk': self.quiz.pk})
        self.login_url = reverse('login')

    def test_successful_json_import(self):
        """
        Testuje poprawny import pytań z pliku JSON (Happy Path).

        Sprawdza, czy po przesłaniu poprawnego pliku JSON pytania i odpowiedzi
        są prawidłowo tworzone w bazie danych i przypisywane do quizu.
        """
        self.client.login(username='testauthor', password='testpassword123')

        json_data = {
            "title": "Importowany Tytuł",
            "questions": [
                {
                    "text": "Jakiego koloru jest niebo?",
                    "explanation": "Zazwyczaj niebieskie.",
                    "question_type": "SINGLE",
                    "answers": [
                        {"text": "Niebieskie", "is_correct": True},
                        {"text": "Czerwone", "is_correct": False},
                        {"text": "Zielone", "is_correct": False}
                    ]
                },
                {
                    "text": "Które z nich są ssakami?",
                    "explanation": "Pies i kot to ssaki.",
                    "question_type": "MULTIPLE",
                    "answers": [
                        {"text": "Pies", "is_correct": True},
                        {"text": "Kot", "is_correct": True},
                        {"text": "Jaszczurka", "is_correct": False}
                    ]
                }
            ]
        }
        
        json_bytes = json.dumps(json_data).encode('utf-8')
        mock_file = SimpleUploadedFile("test_import.json", json_bytes, "application/json")

        self.assertEqual(Question.objects.count(), 0)
        self.assertEqual(Answer.objects.count(), 0)

        response = self.client.post(self.import_url, {'json_file': mock_file})

        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, self.edit_url)

        self.assertEqual(Question.objects.count(), 2)
        self.assertEqual(Answer.objects.count(), 6)

        q1 = Question.objects.get(text="Jakiego koloru jest niebo?")
        q2 = Question.objects.get(text="Które z nich są ssakami?")

        self.assertEqual(q1.quiz, self.quiz)
        self.assertEqual(q1.question_type, 'SINGLE')
        self.assertEqual(q1.answers.count(), 3)
        self.assertTrue(q1.answers.get(text="Niebieskie").is_correct)

        self.assertEqual(q2.question_type, 'MULTIPLE')
        self.assertEqual(q2.answers.filter(is_correct=True).count(), 2)


    def test_import_validation_error_logic(self):
        """
        Testuje zachowanie systemu przy próbie importu logicznie błędnych danych.
        
        Scenariusz: Pytanie typu SINGLE choice z dwiema poprawnymi odpowiedziami.
        Oczekiwany rezultat: Błąd walidacji i brak zmian w bazie.
        """
        self.client.login(username='testauthor', password='testpassword123')

        json_data = {
            "questions": [
                {
                    "text": "Pytanie z błędem",
                    "question_type": "SINGLE",
                    "answers": [
                        {"text": "Poprawna 1", "is_correct": True},
                        {"text": "Poprawna 2", "is_correct": True},
                        {"text": "Błędna", "is_correct": False}
                    ]
                }
            ]
        }
        json_bytes = json.dumps(json_data).encode('utf-8')
        mock_file = SimpleUploadedFile("bad.json", json_bytes, "application/json")

        response = self.client.post(self.import_url, {'json_file': mock_file}, follow=True)

        self.assertEqual(Question.objects.count(), 0)
        self.assertEqual(Answer.objects.count(), 0)

        # Sprawdzamy treść błędu
        self.assertContains(response, "Błąd walidacji")
        self.assertContains(response, "musi mieć dokładnie 1 poprawną odpowiedź")


    def test_import_unauthenticated_user(self):
        """
        Testuje zabezpieczenie widoku importu przed niezalogowanymi użytkownikami.
        """
        mock_file = SimpleUploadedFile("file.json", b"{}", "application/json")
        
        response = self.client.post(self.import_url, {'json_file': mock_file})

        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, f'{self.login_url}?next={self.import_url}')


class QuizTakingTests(TestCase):
    """
    Testy procesu rozwiązywania quizu i naliczania punktów.
    """
    
    def setUp(self):
        """
        Tworzy quiz z jednym pytaniem jednokrotnym i jednym wielokrotnym.
        """
        self.user = User.objects.create_user(username='student', password='password123')
        
        self.quiz = Quiz.objects.create(
            title="Egzamin z wiedzy ogólnej",
            author=self.user,
            visibility='PRIVATE',
            time_limit=10
        )
        
        self.q1 = Question.objects.create(
            quiz=self.quiz,
            text="Stolica Polski?",
            question_type=Question.QuestionType.SINGLE
        )
        self.a1_correct = Answer.objects.create(question=self.q1, text="Warszawa", is_correct=True)
        self.a1_wrong = Answer.objects.create(question=self.q1, text="Kraków", is_correct=False)
        
        self.q2 = Question.objects.create(
            quiz=self.quiz,
            text="Wybierz kolory flagi Polski",
            question_type=Question.QuestionType.MULTIPLE
        )
        self.a2_correct1 = Answer.objects.create(question=self.q2, text="Biały", is_correct=True)
        self.a2_correct2 = Answer.objects.create(question=self.q2, text="Czerwony", is_correct=True)
        self.a2_wrong = Answer.objects.create(question=self.q2, text="Zielony", is_correct=False)

        self.take_url = reverse('quiz-start', kwargs={'pk': self.quiz.pk})

    def test_quiz_perfect_score(self):
        """
        Testuje scenariusz uzyskania 100% punktów.
        """
        self.client.login(username='student', password='password123')

        form_data = {
            f'q_{self.q1.id}': self.a1_correct.id,
            f'q_{self.q2.id}': [self.a2_correct1.id, self.a2_correct2.id]
        }

        response = self.client.post(self.take_url, form_data)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'quizzes/quiz_result.html')

        self.assertEqual(response.context['correct_count'], 2)
        self.assertEqual(response.context['total'], 2)
        self.assertEqual(response.context['score_percent'], 100)
        
    def test_quiz_partial_score(self):
        """
        Testuje scenariusz uzyskania częściowego wyniku (50%).
        
        Użytkownik odpowiada poprawnie na jedno pytanie, a na drugie częściowo
        (co w tym systemie liczone jest jako błąd).
        """
        self.client.login(username='student', password='password123')

        form_data = {
            f'q_{self.q1.id}': self.a1_correct.id,
            f'q_{self.q2.id}': [self.a2_correct1.id]
        }

        response = self.client.post(self.take_url, form_data)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['correct_count'], 1)
        self.assertEqual(response.context['score_percent'], 50)


class QuestionCreationTests(TestCase):
    """
    Testy tworzenia pytań przez formularz (w tym obsługa Formsetów).
    """
    def setUp(self):
        self.user = User.objects.create_user(username='teacher', password='password123')
        self.quiz = Quiz.objects.create(title="Test Quiz", author=self.user)
        self.create_url = reverse('question-create', kwargs={'quiz_pk': self.quiz.pk})
        self.client.login(username='teacher', password='password123')

    def test_create_question_happy_path(self):
        """
        Happy Path: Tworzenie pytania SINGLE z jedną poprawną odpowiedzią.
        """
        data = {
            'text': 'Ile to 2+2?',
            'question_type': 'SINGLE',
            'explanation': 'To proste.',
            # Dane Formsetu (Odpowiedzi)
            'answers-TOTAL_FORMS': '2',
            'answers-INITIAL_FORMS': '0',
            'answers-MIN_NUM_FORMS': '2',
            'answers-MAX_NUM_FORMS': '10',
            
            'answers-0-text': '4',
            'answers-0-is_correct': 'on', # To jest poprawna
            'answers-1-text': '5',
            # 'answers-1-is_correct': brak pola oznacza False w checkboxie
        }
        
        response = self.client.post(self.create_url, data)
        
        # Oczekujemy przekierowania (sukces)
        self.assertEqual(response.status_code, 302)
        
        # Sprawdzamy czy pytanie jest w bazie
        self.assertEqual(Question.objects.count(), 1)
        question = Question.objects.first()
        self.assertEqual(question.text, 'Ile to 2+2?')
        self.assertEqual(question.answers.count(), 2)
        self.assertTrue(question.answers.get(text='4').is_correct)

    def test_create_question_unhappy_path_single_no_correct(self):
        """
        Unhappy Path: Próba utworzenia pytania SINGLE bez poprawnej odpowiedzi.
        """
        data = {
            'text': 'Błędne pytanie',
            'question_type': 'SINGLE',
            # Dane Formsetu
            'answers-TOTAL_FORMS': '2',
            'answers-INITIAL_FORMS': '0',
            'answers-MIN_NUM_FORMS': '2',
            'answers-MAX_NUM_FORMS': '10',
            
            'answers-0-text': 'A',
            'answers-1-text': 'B',
            # Żadna odpowiedź nie ma 'is_correct': 'on'
        }
        
        response = self.client.post(self.create_url, data)
        
        # Oczekujemy statusu 200 (zostajemy na tej samej stronie z błędami)
        self.assertEqual(response.status_code, 200)
        
        # Baza powinna być pusta
        self.assertEqual(Question.objects.count(), 0)
        
        # Sprawdzamy czy wyświetlił się komunikat błędu
        self.assertContains(response, "Pytanie jednokrotnego wyboru musi mieć dokładnie jedną poprawną odpowiedź")

    def test_create_question_unhappy_path_multiple_correct_in_single(self):
        """
        Unhappy Path: Próba utworzenia pytania SINGLE z dwiema poprawnymi odpowiedziami.
        """
        data = {
            'text': 'Błędne pytanie',
            'question_type': 'SINGLE',
            'answers-TOTAL_FORMS': '2',
            'answers-INITIAL_FORMS': '0',
            'answers-MIN_NUM_FORMS': '2',
            'answers-MAX_NUM_FORMS': '10',
            
            'answers-0-text': 'A',
            'answers-0-is_correct': 'on',
            'answers-1-text': 'B',
            'answers-1-is_correct': 'on', # Druga też poprawna -> BŁĄD dla SINGLE
        }
        
        response = self.client.post(self.create_url, data)
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Question.objects.count(), 0)
        self.assertContains(response, "Pytanie jednokrotnego wyboru musi mieć dokładnie jedną poprawną odpowiedź")

class AccountsTests(TestCase):
    """
    Testy funkcjonalności aplikacji accounts.
    """

    def setUp(self):
        """
        Przygotowanie użytkownika testowego do testów logowania i profilu.
        """
        self.user = User.objects.create_user(
            username='testuser_acc',
            email='test@example.com',
            password='testpassword123'
        )
        self.register_url = reverse('register')
        self.login_url = reverse('login')
        self.profile_url = reverse('profile_edit')

    def test_registration_success(self):
        """
        Testuje poprawną rejestrację nowego użytkownika.
        """
        data = {
            'username': 'newuser_reg',
            'email': 'new@example.com',
            # Django UserCreationForm wymaga pól 'password1' i 'password2'
            'password1': 'StrongPassword123!',
            'password2': 'StrongPassword123!',
        }
        
        response = self.client.post(self.register_url, data)
        
        # Jeśli tu nadal jest błąd 200, wypisz błędy formularza, aby je zobaczyć:
        if response.status_code == 200:
            print("Błędy formularza:", response.context['form'].errors)

        # Sprawdzamy czy przekierowano na stronę logowania
        self.assertRedirects(response, self.login_url)
        
        # Sprawdzamy czy użytkownik został utworzony w bazie
        self.assertTrue(User.objects.filter(username='newuser_reg').exists())

    def test_registration_duplicate_username(self):
        """
        Testuje próbę rejestracji na zajętą nazwę użytkownika.
        """
        data = {
            'username': 'testuser_acc', # Ten użytkownik został utworzony w setUp
            'email': 'another@example.com',
            'password1': 'StrongPassword123!',
            'password2': 'StrongPassword123!',
        }
        
        response = self.client.post(self.register_url, data)
        
        # Formularz wyświetlony ponownie z błędami (status 200)
        self.assertEqual(response.status_code, 200)
        
        # Sprawdzamy czy formularz zawiera błędy
        form = response.context['form']
        self.assertTrue(form.errors)

    def test_login_success(self):
        """
        Testuje poprawne logowanie.
        """
        response = self.client.post(self.login_url, {
            'username': 'testuser_acc',
            'password': 'testpassword123'
        })
        
        self.assertRedirects(response, '/', target_status_code=200)
        self.assertIn('_auth_user_id', self.client.session)

    def test_login_failure(self):
        """
        Testuje logowanie z błędnym hasłem.
        """
        response = self.client.post(self.login_url, {
            'username': 'testuser_acc',
            'password': 'wrongpassword'
        })
        
        self.assertEqual(response.status_code, 200)
        self.assertNotIn('_auth_user_id', self.client.session)
        # AuthenticationForm zwykle przekazuje błędy w kontekście pod kluczem 'form'
        self.assertTrue(response.context['form'].errors)

    def test_profile_view_access_authenticated(self):
        """
        Testuje dostęp do edycji profilu dla zalogowanego użytkownika.
        """
        self.client.login(username='testuser_acc', password='testpassword123')
        response = self.client.get(self.profile_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'registration/profile_edit.html')

    def test_profile_view_access_anonymous(self):
        """
        Testuje blokadę dostępu do profilu dla niezalogowanych.
        """
        response = self.client.get(self.profile_url)
        # Sprawdzamy przekierowanie na login z parametrem ?next=
        self.assertRedirects(response, f'{self.login_url}?next={self.profile_url}')

    def test_profile_update_success(self):
        """
        Testuje poprawną aktualizację danych profilowych.
        """
        self.client.login(username='testuser_acc', password='testpassword123')
        
        new_data = {
            'first_name': 'Jan',
            'last_name': 'Kowalski',
            'email': 'nowy@email.com'
        }
        
        response = self.client.post(self.profile_url, new_data)
        
        # Oczekujemy przekierowania na tę samą stronę (sukces)
        self.assertRedirects(response, self.profile_url)
        
        # Odświeżamy obiekt z bazy i sprawdzamy zmiany
        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, 'Jan')
        self.assertEqual(self.user.last_name, 'Kowalski')
        self.assertEqual(self.user.email, 'nowy@email.com')


class QuizAccessTests(TestCase):
    """
    Testy sprawdzające logikę dostępu do quizów (Publiczne, Prywatne, Udostępnione).
    """

    def setUp(self):
        # Tworzymy dwóch użytkowników
        self.user_a = User.objects.create_user(username='autor', password='password123')
        self.user_b = User.objects.create_user(username='inny_user', password='password123')

        # Tworzymy quizy
        self.quiz_public = Quiz.objects.create(
            title="Quiz Publiczny",
            author=self.user_a,
            visibility='PUBLIC'
        )
        
        self.quiz_private = Quiz.objects.create(
            title="Quiz Prywatny",
            author=self.user_a,
            visibility='PRIVATE'
        )

        
        # Widok quiz_take_view przekierowuje (302) jeśli quiz nie ma pytań.
        # Aby otrzymać status 200, quiz musi mieć przynajmniej jedno pytanie.
        Question.objects.create(quiz=self.quiz_public, text="Pytanie publiczne", question_type='SINGLE')
        Question.objects.create(quiz=self.quiz_private, text="Pytanie prywatne", question_type='SINGLE')
        # --------------------------------------------

        # URL-e
        self.home_url = reverse('home')
        self.my_quizzes_url = reverse('my-quizzes')

    def test_public_quiz_access(self):
        """
        Dostęp do quizu publicznego.
        - Jest widoczny na stronie głównej.
        - can_view zwraca True.
        - Widoki detail i start są dostępne (status 200).
        """
        # 1. Sprawdź widoczność w home_view
        response = self.client.get(self.home_url)
        self.assertContains(response, self.quiz_public.title)
        
        # 2. Sprawdź funkcję logiczną _can_view_quiz (metoda modelu can_view)
        # Nawet niezalogowany (lub user_b) powinien mieć dostęp
        self.assertTrue(self.quiz_public.can_view(self.user_b))

        # 3. Sprawdź dostęp do widoków (jako zalogowany user_b)
        self.client.login(username='inny_user', password='password123')
        
        detail_url = reverse('quiz-detail', kwargs={'pk': self.quiz_public.pk})
        take_url = reverse('quiz-start', kwargs={'pk': self.quiz_public.pk})

        response_detail = self.client.get(detail_url)
        self.assertEqual(response_detail.status_code, 200)

        response_take = self.client.get(take_url)
        self.assertEqual(response_take.status_code, 200)

    def test_private_quiz_logic(self):
        """
        Logika quizu prywatnego.
        - Nie jest widoczny na home_view.
        - can_view zwraca False dla nieuprawnionego (User B).
        - Próba wejścia skutkuje przekierowaniem.
        """
        # 1. Sprawdź brak widoczności w home_view
        response = self.client.get(self.home_url)
        self.assertNotContains(response, self.quiz_private.title)

        # 2. Sprawdź funkcję logiczną
        self.assertFalse(self.quiz_private.can_view(self.user_b))

        # 3. Próba wejścia na widok (jako User B)
        self.client.login(username='inny_user', password='password123')
        detail_url = reverse('quiz-detail', kwargs={'pk': self.quiz_private.pk})
        
        response = self.client.get(detail_url)
        
        # Oczekujemy przekierowania (do home, bo brak uprawnień)
        self.assertRedirects(response, self.home_url)
        
        # Opcjonalnie: sprawdź czy pojawił się komunikat (Messages framework)
        messages = list(response.wsgi_request._messages)
        self.assertTrue(any("Nie masz uprawnień" in str(m) for m in messages))

    def test_shared_quiz_access(self):
        """
        Dostęp do quizu udostępnionego.
        - Nadajemy uprawnienie VIEWER dla User B.
        - Quiz pojawia się w 'Moje Quizy' (sekcja udostępnione).
        - can_view zwraca True.
        - Użytkownik B może wejść na widoki.
        """
        # 1. Autor (A) udostępnia quiz użytkownikowi B
        # Używamy modelu QuizUserPermission zamiast usuniętego pola shared_with
        QuizUserPermission.objects.create(
            quiz=self.quiz_private,
            user=self.user_b,
            role='VIEWER'
        )

        # 2. Logujemy się jako User B
        self.client.login(username='inny_user', password='password123')

        # 3. Sprawdź czy quiz jest na liście 'Moje Quizy' (shared_quizzes)
        response = self.client.get(self.my_quizzes_url)
        self.assertContains(response, self.quiz_private.title)
        # Sprawdzamy czy trafił do odpowiedniej sekcji w kontekście szablonu
        self.assertIn(self.quiz_private, response.context['shared_quizzes'])

        # 4. Sprawdź funkcję logiczną
        # User B ma teraz wpis w tabeli uprawnień, więc powinno być True
        self.assertTrue(self.quiz_private.can_view(self.user_b))

        # 5. Sprawdź wejście na widoki
        detail_url = reverse('quiz-detail', kwargs={'pk': self.quiz_private.pk})
        take_url = reverse('quiz-start', kwargs={'pk': self.quiz_private.pk})

        response_detail = self.client.get(detail_url)
        self.assertEqual(response_detail.status_code, 200)

        response_take = self.client.get(take_url)
        self.assertEqual(response_take.status_code, 200)