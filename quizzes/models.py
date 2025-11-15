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
    def __str__(self): return self.title

class Question(models.Model):
    # 🔽 NOWE POLA: Definicja typów pytań
    class QuestionType(models.TextChoices):
        SINGLE = 'SINGLE', 'Jednokrotny wybór'
        MULTIPLE = 'MULTIPLE', 'Wielokrotny wybór'

    quiz = models.ForeignKey(Quiz, related_name='questions', on_delete=models.CASCADE)
    text = models.TextField()
    explanation = models.TextField(blank=True, default="")
    
    # 🔽 NOWE POLE: przechowuje typ pytania, domyślnie jednokrotny wybór
    question_type = models.CharField(
        max_length=10,
        choices=QuestionType.choices,
        default=QuestionType.SINGLE
    )
    # 🔼 KONIEC NOWEGO POLA

class Answer(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='answers')
    text = models.CharField(max_length=255)
    is_correct = models.BooleanField(default=False)
    def __str__(self): return self.text