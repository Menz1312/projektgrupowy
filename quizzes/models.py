# quizzes/models.py
from django.db import models
from django.conf import settings

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
    
    # --- NOWE POLE ---
    shared_with = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name='shared_quizzes', # Umożliwia user.shared_quizzes.all()
        blank=True, # Udostępnianie jest opcjonalne
        verbose_name="Udostępnij dla"
    )
    # -----------------

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