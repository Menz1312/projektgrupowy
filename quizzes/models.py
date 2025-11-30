# quizzes/models.py
from django.db import models
from django.conf import settings

class QuizGroup(models.Model):
    name = models.CharField(max_length=100, verbose_name="Nazwa grupy")
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='owned_groups',
        verbose_name="Właściciel"
    )
    members = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name='group_memberships',
        verbose_name="Członkowie grupy"
    )

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Grupa użytkowników"
        verbose_name_plural = "Grupy użytkowników"
        ordering = ['name']

class Quiz(models.Model):
    class Visibility(models.TextChoices):
        PUBLIC = 'PUBLIC', 'Publiczny'
        PRIVATE = 'PRIVATE', 'Prywatny'
    
    title = models.CharField(max_length=255)
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    visibility = models.CharField(max_length=10, choices=Visibility.choices, default=Visibility.PRIVATE)
    
    time_limit = models.IntegerField(
        default=0, 
        verbose_name="Limit czasu (w minutach)",
        help_text="Ustaw 0, aby wyłączyć limit czasu."
    )
    
    shared_with = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name='shared_quizzes',
        blank=True,
        verbose_name="Udostępnij dla (użytkownicy)"
    )

    shared_groups = models.ManyToManyField(
        QuizGroup,
        related_name='shared_quizzes',
        blank=True,
        verbose_name="Udostępnij dla (grupy)"
    )

    def __str__(self): return self.title

class Question(models.Model):
    # (reszta modelu Question bez zmian)
    class QuestionType(models.TextChoices):
        SINGLE = 'SINGLE', 'Jednokrotny wybór'
        MULTIPLE = 'MULTIPLE', 'Wielokrotny wybór'

    quiz = models.ForeignKey(Quiz, related_name='questions', on_delete=models.CASCADE)
    text = models.TextField()
    explanation = models.TextField(blank=True, default="")
    
    question_type = models.CharField(
        max_length=10,
        choices=QuestionType.choices,
        default=QuestionType.SINGLE
    )

class Answer(models.Model):
    # (model Answer bez zmian)
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='answers')
    text = models.CharField(max_length=255)
    is_correct = models.BooleanField(default=False)
    def __str__(self): return self.text

# --- NOWY MODEL DO PRZECHOWYWANIA PRÓB ---
class QuizAttempt(models.Model):
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name="attempts", verbose_name="Quiz")
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, # Zachowaj próbę, nawet jeśli użytkownik zostanie usunięty
        null=True, 
        blank=True, # Zezwalaj na próby anonimowe
        related_name="attempts",
        verbose_name="Użytkownik"
    )
    score = models.IntegerField(verbose_name="Wynik (%)")
    correct_count = models.IntegerField(verbose_name="Poprawne odpowiedzi")
    total_questions = models.IntegerField(verbose_name="Liczba pytań")
    time_over = models.BooleanField(default=False, verbose_name="Przekroczono czas")
    timestamp = models.DateTimeField(auto_now_add=True, verbose_name="Data podejścia")

    def __str__(self):
        user_str = self.user.username if self.user else "Anonim"
        return f"Próba: {self.quiz.title} - {user_str} ({self.score}%)"

    class Meta:
        verbose_name = "Próba (Attempt)"
        verbose_name_plural = "Próby (Attempts)"
        ordering = ['-timestamp'] # Najnowsze próby na górze