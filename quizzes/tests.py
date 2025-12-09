# quizzes/tests.py
import json
from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from .models import Quiz, Question, Answer

# Pobieramy model użytkownika zdefiniowany w settings.py
User = get_user_model()


class QuizImportTests(TestCase):
    
    def setUp(self):
        """
        Ta metoda jest uruchamiana przed każdym pojedynczym testem w tej klasie.
        Tworzy izolowane środowisko dla każdego testu.
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
        Testuje: Import pytań z poprawnego pliku JSON (Happy Path)
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
        Testuje: Import (negatywny) - błąd walidacji logiki JSON
        (Pytanie SINGLE z 2 poprawnymi odpowiedziami)
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
        Testuje: Import (negatywny) - użytkownik niezalogowany
        """
        mock_file = SimpleUploadedFile("file.json", b"{}", "application/json")
        
        response = self.client.post(self.import_url, {'json_file': mock_file})

        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, f'{self.login_url}?next={self.import_url}')


class QuizTakingTests(TestCase):
    
    def setUp(self):
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
        Unhappy Path: Pytanie SINGLE bez poprawnej odpowiedzi.
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
        Unhappy Path: Pytanie SINGLE z dwoma poprawnymi odpowiedziami.
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


# --- NOWE TESTY KONTA UŻYTKOWNIKA (REJESTRACJA, LOGOWANIE, PROFIL) ---
# --- POPRAWIONE TESTY KONTA UŻYTKOWNIKA ---
class AccountsTests(TestCase):

    def setUp(self):
        # Tworzymy użytkownika testowego do wykorzystania w testach logowania i profilu
        self.user = User.objects.create_user(
            username='testuser_acc',
            email='test@example.com',
            password='testpassword123'
        )
        self.register_url = reverse('register')
        self.login_url = reverse('login')
        self.profile_url = reverse('profile_edit')

    # --- 1. REJESTRACJA ---

    def test_registration_success(self):
        """
        Testuje: Rejestracja z poprawnymi danymi tworzy użytkownika i przekierowuje do logowania.
        """
        data = {
            'username': 'newuser_reg',
            'email': 'new@example.com',
            # POPRAWKA: Django UserCreationForm wymaga pól 'password1' i 'password2'
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
        Testuje: Próba rejestracji na zajętą nazwę użytkownika zwraca błąd walidacji.
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

    # --- 2. LOGOWANIE ---

    def test_login_success(self):
        """
        Testuje: Poprawne logowanie przekierowuje na stronę główną i tworzy sesję.
        """
        response = self.client.post(self.login_url, {
            'username': 'testuser_acc',
            'password': 'testpassword123'
        })
        
        self.assertRedirects(response, '/', target_status_code=200)
        self.assertIn('_auth_user_id', self.client.session)

    def test_login_failure(self):
        """
        Testuje: Logowanie złym hasłem nie tworzy sesji i wyświetla błąd.
        """
        response = self.client.post(self.login_url, {
            'username': 'testuser_acc',
            'password': 'wrongpassword'
        })
        
        self.assertEqual(response.status_code, 200)
        self.assertNotIn('_auth_user_id', self.client.session)
        # AuthenticationForm zwykle przekazuje błędy w kontekście pod kluczem 'form'
        self.assertTrue(response.context['form'].errors)

    # --- 3. EDYCJA PROFILU ---

    def test_profile_view_access_authenticated(self):
        """
        Testuje: Zalogowany użytkownik ma dostęp do edycji profilu.
        """
        self.client.login(username='testuser_acc', password='testpassword123')
        response = self.client.get(self.profile_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'registration/profile_edit.html')

    def test_profile_view_access_anonymous(self):
        """
        Testuje: Niezalogowany użytkownik jest przekierowywany do logowania.
        """
        response = self.client.get(self.profile_url)
        # Sprawdzamy przekierowanie na login z parametrem ?next=
        self.assertRedirects(response, f'{self.login_url}?next={self.profile_url}')

    def test_profile_update_success(self):
        """
        Testuje: Wysłanie formularza edycji profilu aktualizuje dane w bazie.
        """
        self.client.login(username='testuser_acc', password='testpassword123')
        
        new_data = {
            'first_name': 'Jan',
            'last_name': 'Kowalski',
            'email': 'nowy@email.com'
        }
        
        response = self.client.post(self.profile_url, new_data)
        
        # Oczekujemy przekierowania na tę samą stronę (sukces) - w widoku profile_edit_view jest return redirect('profile_edit')
        self.assertRedirects(response, self.profile_url)
        
        # Odświeżamy obiekt z bazy i sprawdzamy zmiany
        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, 'Jan')
        self.assertEqual(self.user.last_name, 'Kowalski')
        self.assertEqual(self.user.email, 'nowy@email.com')