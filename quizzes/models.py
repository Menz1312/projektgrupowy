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
    
    title = models.CharField(max_length=255, verbose_name="Tytuł")
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name="Autor")
    
    visibility = models.CharField(
        max_length=10, 
        choices=Visibility.choices, 
        default=Visibility.PRIVATE,
        verbose_name="Widoczność"
    )
    
    time_limit = models.IntegerField(
        default=0, 
        verbose_name="Limit czasu (w minutach)",
        help_text="Ustaw 0, aby wyłączyć limit czasu."
    )

    instant_feedback = models.BooleanField(
        default=False, 
        verbose_name="Natychmiastowe odpowiedzi",
        help_text="Jeśli zaznaczone, użytkownik zobaczy poprawne odpowiedzi po każdym pytaniu."
    )
    
    # Relacje zdefiniowane przez modele pośrednie (Through Models)
    # Pozwala to na dodanie dodatkowych pól (jak 'role') do relacji
    users_permissions = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        through='QuizUserPermission',
        related_name='quiz_access',
        blank=True,
        verbose_name="Uprawnienia użytkowników"
    )

    groups_permissions = models.ManyToManyField(
        QuizGroup,
        through='QuizGroupPermission',
        related_name='quiz_access',
        blank=True,
        verbose_name="Uprawnienia grup"
    )

    def __str__(self): return self.title

    def can_edit(self, user):
        """Sprawdza, czy użytkownik może edytować ten quiz."""
        if not user.is_authenticated:
            return False
        if user == self.author:
            return True
        # Sprawdź czy jest w tabeli uprawnień jako EDITOR
        return self.quizuserpermission_set.filter(user=user, role='EDITOR').exists()

    def can_view(self, user):
        """Sprawdza, czy użytkownik ma dostęp (podgląd lub edycja)."""
        if self.visibility == 'PUBLIC': return True
        if not user.is_authenticated: return False
        if self.can_edit(user): return True
        
        # Sprawdzenie bezpośrednie (VIEWER)
        if self.quizuserpermission_set.filter(user=user).exists():
            return True
            
        # Sprawdzenie przez grupy
        # Pobieramy grupy użytkownika i sprawdzamy czy któraś ma uprawnienia do tego quizu
        user_groups = user.group_memberships.all()
        if self.quizgrouppermission_set.filter(group__in=user_groups).exists():
            return True
            
        return False

# --- MODELE POŚREDNIE (TABELE ŁĄCZĄCE Z ROLĄ) ---

class QuizUserPermission(models.Model):
    class Role(models.TextChoices):
        VIEWER = 'VIEWER', 'Może rozwiązywać'
        EDITOR = 'EDITOR', 'Może edytować'

    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name="Użytkownik")
    role = models.CharField(max_length=10, choices=Role.choices, default=Role.VIEWER, verbose_name="Uprawnienie")

    class Meta:
        unique_together = ('quiz', 'user') # Jeden user może mieć tylko jedną rolę w danym quizie
        verbose_name = "Uprawnienie użytkownika"

class QuizGroupPermission(models.Model):
    class Role(models.TextChoices):
        VIEWER = 'VIEWER', 'Może rozwiązywać'
        EDITOR = 'EDITOR', 'Może edytować (członkowie)' # Zazwyczaj grupy tylko rozwiązują, ale dajmy opcję

    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE)
    group = models.ForeignKey(QuizGroup, on_delete=models.CASCADE, verbose_name="Grupa")
    role = models.CharField(max_length=10, choices=Role.choices, default=Role.VIEWER, verbose_name="Uprawnienie")

    class Meta:
        unique_together = ('quiz', 'group')
        verbose_name = "Uprawnienie grupy"


class Question(models.Model):
    class QuestionType(models.TextChoices):
        SINGLE = 'SINGLE', 'Jednokrotny wybór'
        MULTIPLE = 'MULTIPLE', 'Wielokrotny wybór'

    quiz = models.ForeignKey(Quiz, related_name='questions', on_delete=models.CASCADE)
    text = models.TextField(verbose_name="Treść pytania")
    explanation = models.TextField(blank=True, default="", verbose_name="Wyjaśnienie")
    
    question_type = models.CharField(
        max_length=10,
        choices=QuestionType.choices,
        default=QuestionType.SINGLE,
        verbose_name="Typ pytania"
    )

    def __str__(self): return self.text

class Answer(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='answers')
    text = models.CharField(max_length=255, verbose_name="Treść odpowiedzi")
    is_correct = models.BooleanField(default=False, verbose_name="Czy poprawna")
    def __str__(self): return self.text

class QuizAttempt(models.Model):
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name="attempts", verbose_name="Quiz")
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name="attempts",
        verbose_name="Użytkownik"
    )
    score = models.IntegerField(verbose_name="Wynik (%)")
    correct_count = models.IntegerField(verbose_name="Poprawne odpowiedzi")
    total_questions = models.IntegerField(verbose_name="Liczba pytań")
    time_over = models.BooleanField(default=False, verbose_name="Przekroczono czas")
    timestamp = models.DateTimeField(auto_now_add=True, verbose_name="Data podejścia")

    class Meta:
        verbose_name = "Próba (Attempt)"
        verbose_name_plural = "Próby (Attempts)"
        ordering = ['-timestamp']