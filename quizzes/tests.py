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