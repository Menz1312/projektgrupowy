# quizzes/models.py
from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator

class QuizGroup(models.Model):
    """
    Reprezentuje grupę użytkowników, którym można udostępniać quizy.

    Attributes:
        name (str): Nazwa grupy (maks. 100 znaków).
        owner (User): Użytkownik, który jest właścicielem i zarządcą grupy.
        members (QuerySet[User]): Zbiór użytkowników należących do grupy.
    """
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
    """
    Główny model reprezentujący Quiz.

    Attributes:
        title (str): Tytuł quizu.
        author (User): Autor quizu (właściciel).
        visibility (str): Widoczność quizu ('PUBLIC' lub 'PRIVATE').
        time_limit (int): Limit czasu na rozwiązanie quizu w minutach (0 oznacza brak limitu).
        questions_count_limit (int): Liczba pytań losowanych do jednego podejścia (domyślnie 10, zakres 1-30).
        instant_feedback (bool): Czy pokazywać poprawne odpowiedzi natychmiast po zaznaczeniu.
        users_permissions (QuerySet[User]): Użytkownicy z przypisanymi uprawnieniami (przez model pośredni).
        groups_permissions (QuerySet[QuizGroup]): Grupy z przypisanymi uprawnieniami (przez model pośredni).
    """
    class Visibility(models.TextChoices):
        """Dostępne opcje widoczności quizu."""
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

    questions_count_limit = models.IntegerField(
        default=10,
        verbose_name="Liczba pytań w podejściu",
        validators=[MinValueValidator(1), MaxValueValidator(30)],
        help_text="Ustal, ile pytań ma zostać wylosowanych do jednego podejścia (zakres: 1-30)."
    )

    instant_feedback = models.BooleanField(
        default=False, 
        verbose_name="Natychmiastowe odpowiedzi",
        help_text="Jeśli zaznaczone, użytkownik zobaczy poprawne odpowiedzi po każdym pytaniu."
    )
    
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

    def can_edit(self, user) -> bool:
        """
        Sprawdza, czy dany użytkownik ma uprawnienia do edycji tego quizu.

        Args:
            user (User): Obiekt użytkownika do sprawdzenia.

        Returns:
            bool: True, jeśli użytkownik jest autorem lub posiada rolę 'EDITOR' (bezpośrednio),
                  w przeciwnym razie False.
        """
        if not user.is_authenticated:
            return False
        if user == self.author:
            return True
        # Sprawdź czy jest w tabeli uprawnień jako EDITOR
        return self.quizuserpermission_set.filter(user=user, role='EDITOR').exists()

    def can_view(self, user) -> bool:
        """
        Sprawdza, czy użytkownik ma dostęp (do podglądu lub edycji) do quizu.

        Dostęp mają:
        
        * Wszyscy użytkownicy dla quizów publicznych.
        * Autor quizu.
        * Użytkownicy z przypisanym uprawnieniem (VIEWER lub EDITOR).
        * Członkowie grup, które mają przypisane uprawnienie do tego quizu.

        Args:
            user (User): Obiekt użytkownika, który próbuje uzyskać dostęp.

        Returns:
            bool: True, jeśli użytkownik może oglądać quiz, False w przeciwnym razie.
        """
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
    """
    Model pośredni łączący Quiz i Użytkownika, definiujący rolę (uprawnienie).

    Attributes:
        quiz (Quiz): Quiz, którego dotyczy uprawnienie.
        user (User): Użytkownik, któremu nadano uprawnienie.
        role (str): Rola użytkownika ('VIEWER' lub 'EDITOR').
    """
    class Role(models.TextChoices):
        """Dostępne role dla użytkownika w kontekście quizu."""
        VIEWER = 'VIEWER', 'Może rozwiązywać'
        EDITOR = 'EDITOR', 'Może edytować'

    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name="Użytkownik")
    role = models.CharField(max_length=10, choices=Role.choices, default=Role.VIEWER, verbose_name="Uprawnienie")

    class Meta:
        unique_together = ('quiz', 'user') # Jeden user może mieć tylko jedną rolę w danym quizie
        verbose_name = "Uprawnienie użytkownika"

class QuizGroupPermission(models.Model):
    """
    Model pośredni łączący Quiz i Grupę, definiujący uprawnienia dla całej grupy.

    Attributes:
        quiz (Quiz): Quiz, którego dotyczy uprawnienie.
        group (QuizGroup): Grupa, której nadano uprawnienie.
        role (str): Rola przypisana grupie (zazwyczaj 'VIEWER' lub 'EDITOR').
    """
    class Role(models.TextChoices):
        """Dostępne role dla grupy."""
        VIEWER = 'VIEWER', 'Może rozwiązywać'
        EDITOR = 'EDITOR', 'Może edytować (członkowie)'

    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE)
    group = models.ForeignKey(QuizGroup, on_delete=models.CASCADE, verbose_name="Grupa")
    role = models.CharField(max_length=10, choices=Role.choices, default=Role.VIEWER, verbose_name="Uprawnienie")

    class Meta:
        unique_together = ('quiz', 'group')
        verbose_name = "Uprawnienie grupy"


class Question(models.Model):
    """
    Pojedyncze pytanie w quizie.

    Attributes:
        quiz (Quiz): Quiz, do którego należy pytanie.
        text (str): Treść pytania.
        explanation (str): Opcjonalne wyjaśnienie wyświetlane po rozwiązaniu.
        question_type (str): Typ pytania ('SINGLE' lub 'MULTIPLE').
    """
    class QuestionType(models.TextChoices):
        """Dostępne typy pytań."""
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
    """
    Odpowiedź do pytania.

    Attributes:
        question (Question): Pytanie, do którego należy odpowiedź.
        text (str): Treść odpowiedzi.
        is_correct (bool): Czy ta odpowiedź jest poprawna.
    """
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='answers')
    text = models.CharField(max_length=255, verbose_name="Treść odpowiedzi")
    is_correct = models.BooleanField(default=False, verbose_name="Czy poprawna")
    def __str__(self): return self.text

class QuizAttempt(models.Model):
    """
    Zapis pojedynczego podejścia użytkownika do quizu.

    Attributes:
        quiz (Quiz): Quiz, który był rozwiązywany.
        user (User): Użytkownik, który rozwiązywał quiz (może być NULL dla anonimowych/usuniętych).
        score (int): Wynik procentowy (0-100).
        correct_count (int): Liczba poprawnych odpowiedzi.
        total_questions (int): Łączna liczba pytań w tym podejściu.
        time_over (bool): Czy czas upłynął przed zakończeniem.
        timestamp (datetime): Data i czas podejścia.
    """
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