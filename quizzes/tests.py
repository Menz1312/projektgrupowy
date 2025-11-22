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
        # --- KROK 1: ARRANGE (Przygotowanie) ---
        
        # 1a. Zaloguj klienta testowego jako autora quizu
        self.client.login(username='testauthor', password='testpassword123')

        # 1b. Zdefiniuj poprawną strukturę danych JSON
        json_data = {
            "title": "Importowany Tytuł (ignorowany przez widok)",
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
        
        # 1c. Przekonwertuj słownik Pythona na bajty (UTF-8), tak jak robi to przeglądarka
        json_bytes = json.dumps(json_data).encode('utf-8')

        # 1d. Stwórz "fałszywy" plik, który Django może przetworzyć
        mock_file = SimpleUploadedFile(
            name="test_import.json",
            content=json_bytes,
            content_type="application/json"
        )

        # Sprawdź stan początkowy bazy testowej (powinno być 0)
        self.assertEqual(Question.objects.count(), 0)
        self.assertEqual(Answer.objects.count(), 0)

        # --- KROK 2: ACT (Działanie) ---
        # Wysłanie żądania POST z plikiem
        response = self.client.post(self.import_url, {'json_file': mock_file})

        # --- KROK 3: ASSERT (Sprawdzenie) ---
        
        # 3a. Sprawdź, czy nastąpiło przekierowanie (HTTP 302) na stronę edycji quizu
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, self.edit_url)

        # 3b. Sprawdź, czy obiekty faktycznie utworzyły się w bazie
        self.assertEqual(Question.objects.count(), 2)
        # 3 odpowiedzi dla pytania 1 + 3 odpowiedzi dla pytania 2 = 6 odpowiedzi
        self.assertEqual(Answer.objects.count(), 6)

        # 3c. (Bardziej szczegółowo) Sprawdźmy, czy pytania są poprawne
        q1 = Question.objects.get(text="Jakiego koloru jest niebo?")
        q2 = Question.objects.get(text="Które z nich są ssakami?")

        self.assertEqual(q1.quiz, self.quiz) # Czy pytanie jest podpięte do właściwego quizu
        self.assertEqual(q1.question_type, 'SINGLE')
        self.assertEqual(q1.answers.count(), 3)
        self.assertEqual(q1.answers.filter(is_correct=True).first().text, "Niebieskie")

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

        # Używamy `follow=True`, aby od razu pobrać stronę, na którą zostaliśmy
        # przekierowani (stronę edycji quizu z komunikatem błędu).
        response = self.client.post(self.import_url, {'json_file': mock_file}, follow=True)

        # Sprawdzamy, czy transakcja została wycofana (nic się nie dodało do bazy)
        self.assertEqual(Question.objects.count(), 0)
        self.assertEqual(Answer.objects.count(), 0)

        # Sprawdzamy, czy strona (po przekierowaniu) zawiera komunikaty błędów
        # status_code=200 jest sprawdzany automatycznie przez assertContains
        self.assertContains(response, "Błąd walidacji")
        self.assertContains(response, "Musi mieć dokładnie 1 poprawną odpowiedź")


    def test_import_unauthenticated_user(self):
        """
        Testuje: Import (negatywny) - użytkownik niezalogowany
        """
        mock_file = SimpleUploadedFile("file.json", b"{}", "application/json")
        
        # NIE logujemy się
        response = self.client.post(self.import_url, {'json_file': mock_file})

        # Sprawdzamy, czy zostaliśmy przekierowani (302) do strony logowania
        self.assertEqual(response.status_code, 302)
        # Sprawdzamy, czy URL logowania zawiera poprawny parametr "next"
        self.assertRedirects(response, f'{self.login_url}?next={self.import_url}')

class QuizTakingTests(TestCase):
    
    def setUp(self):
        # 1. Tworzymy użytkownika
        self.user = User.objects.create_user(username='student', password='password123')
        
        # 2. Tworzymy quiz
        self.quiz = Quiz.objects.create(
            title="Egzamin z wiedzy ogólnej",
            author=self.user,
            visibility='PRIVATE', # Autor widzi swój prywatny quiz
            time_limit=10
        )
        
        # 3. Tworzymy Pytanie 1 (Jednokrotny wybór - SINGLE)
        self.q1 = Question.objects.create(
            quiz=self.quiz,
            text="Stolica Polski?",
            question_type=Question.QuestionType.SINGLE
        )
        self.a1_correct = Answer.objects.create(question=self.q1, text="Warszawa", is_correct=True)
        self.a1_wrong = Answer.objects.create(question=self.q1, text="Kraków", is_correct=False)
        
        # 4. Tworzymy Pytanie 2 (Wielokrotny wybór - MULTIPLE)
        self.q2 = Question.objects.create(
            quiz=self.quiz,
            text="Wybierz kolory flagi Polski",
            question_type=Question.QuestionType.MULTIPLE
        )
        self.a2_correct1 = Answer.objects.create(question=self.q2, text="Biały", is_correct=True)
        self.a2_correct2 = Answer.objects.create(question=self.q2, text="Czerwony", is_correct=True)
        self.a2_wrong = Answer.objects.create(question=self.q2, text="Zielony", is_correct=False)

        # URL do rozwiązywania tego quizu
        self.take_url = reverse('quiz-start', kwargs={'pk': self.quiz.pk})

    def test_quiz_perfect_score(self):
        """
        Testuje User Story: Rozwiązanie quizu (Happy Path - 100% poprawnych).
        """
        self.client.login(username='student', password='password123')

        # Przygotowujemy dane formularza (odpowiedzi użytkownika)
        # Dla SINGLE: wartość to ID wybranej odpowiedzi
        # Dla MULTIPLE: lista ID wybranych odpowiedzi
        form_data = {
            f'q_{self.q1.id}': self.a1_correct.id,
            f'q_{self.q2.id}': [self.a2_correct1.id, self.a2_correct2.id]
        }

        # Wysłanie formularza
        response = self.client.post(self.take_url, form_data)

        # 1. Weryfikacja: Czy strona się załadowała (200 OK) i używa szablonu wyników
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'quizzes/quiz_result.html')

        # 2. Weryfikacja logiki: Czy poprawnie policzono punkty
        # Dane te są przekazywane w kontekście szablonu
        self.assertEqual(response.context['correct_count'], 2)
        self.assertEqual(response.context['total'], 2)
        self.assertEqual(response.context['score_percent'], 100)
        
        # Sprawdzenie czy w szczegółach pytania jest flaga is_correct=True
        details = response.context['details']
        self.assertTrue(details[0]['is_correct']) # Pierwsze pytanie
        self.assertTrue(details[1]['is_correct']) # Drugie pytanie

    def test_quiz_partial_score(self):
        """
        Testuje User Story: Rozwiązanie quizu (Błędne odpowiedzi - 50%).
        """
        self.client.login(username='student', password='password123')

        form_data = {
            f'q_{self.q1.id}': self.a1_correct.id,      # Dobrze
            f'q_{self.q2.id}': [self.a2_correct1.id]    # Źle (brak drugiej poprawnej odpowiedzi w pytaniu wielokrotnym)
        }

        response = self.client.post(self.take_url, form_data)

        self.assertEqual(response.status_code, 200)
        
        # Oczekujemy 1 punktu na 2 możliwe (50%)
        # (Logika w views.py: pytanie wielokrotne jest poprawne TYLKO gdy zaznaczono wszystkie dobre i żadnej złej)
        self.assertEqual(response.context['correct_count'], 1)
        self.assertEqual(response.context['total'], 2)
        self.assertEqual(response.context['score_percent'], 50)