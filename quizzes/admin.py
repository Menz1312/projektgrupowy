# quizzes/admin.py
from django.contrib import admin
from .models import Quiz, Question, Answer, QuizAttempt

# Definicja "inline" dla odpowiedzi - aby odpowiedzi edytować
# bezpośrednio na stronie edycji pytania.
class AnswerInline(admin.TabularInline):
    model = Answer
    extra = 2  # Pokaż 2 puste pola na nowe odpowiedzi
    min_num = 2  # Wymagaj minimum 2 odpowiedzi (zgodnie z forms.py)
    max_num = 10 # Ogranicz do 10 odpowiedzi (zgodnie z forms.py)
    fields = ('text', 'is_correct') # Pokaż tylko te pola

# Definicja "inline" dla pytań - aby pytania edytować
# bezpośrednio na stronie edycji quizu.
class QuestionInline(admin.TabularInline):
    model = Question
    extra = 1  # Pokaż 1 puste pole na nowe pytanie
    
    # Pokaż tylko te pola w trybie inline (reszta będzie w QuestionAdmin)
    fields = ('text', 'question_type') 
    
    # Dodaje link "Zmień" przy każdym pytaniu, aby przejść
    # do pełnego edytora QuestionAdmin (gdzie są odpowiedzi)
    show_change_link = True 

# Konfiguracja panelu administratora dla modelu Question
@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ('text', 'quiz', 'question_type')
    list_filter = ('quiz', 'question_type')
    search_fields = ('text', 'quiz__title')
    
    # Osadź edytor odpowiedzi w edytorze pytania
    inlines = [AnswerInline]

# Konfiguracja panelu administratora dla modelu Quiz
@admin.register(Quiz)
class QuizAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'visibility', 'time_limit', 'question_count')
    list_filter = ('visibility', 'author')
    search_fields = ('title', 'author__username')
    
    # Osadź edytor pytań w edytorze quizu
    inlines = [QuestionInline]
    
    # Użyj lepszego widgetu dla pola many-to-many (shared_with)
    filter_horizontal = ('shared_with',)

    # Optymalizacja zapytania i dodanie własnej kolumny
    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        # Optymalizacja: pobierz powiązane pytania z góry
        queryset = queryset.prefetch_related('questions')
        return queryset

    def question_count(self, obj):
        # Wyświetla liczbę pytań w kolumnie
        return obj.questions.count()
    
    question_count.short_description = 'Liczba pytań'

# --- NOWA REJESTRACJA DLA PRÓB (ATTEMPTS) ---
@admin.register(QuizAttempt)
class QuizAttemptAdmin(admin.ModelAdmin):
    list_display = ('quiz', 'user', 'score', 'timestamp', 'time_over')
    list_filter = ('quiz', 'user', 'time_over', 'timestamp')
    search_fields = ('quiz__title', 'user__username')

    # Ustaw pola tylko do odczytu, ponieważ admin nie powinien
    # móc ręcznie edytować historycznych wyników.
    readonly_fields = [
        'quiz', 'user', 'score', 'correct_count', 
        'total_questions', 'time_over', 'timestamp'
    ]

    # Blokuj możliwość ręcznego dodawania prób przez panel admina
    def has_add_permission(self, request):
        return False

    # Opcjonalnie: blokuj też możliwość zmiany (admin będzie mógł tylko usuwać)
    def has_change_permission(self, request, obj=None):
        return False