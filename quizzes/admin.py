# quizzes/admin.py
"""
Moduł konfiguracji panelu administracyjnego dla aplikacji quizzes.

Rejestruje modele Quiz, Question, Answer, QuizGroup oraz powiązane
tabele uprawnień, umożliwiając zarządzanie nimi z poziomu panelu Django Admin.
"""

from django.contrib import admin
from .models import Quiz, Question, Answer, QuizAttempt, QuizGroup, QuizUserPermission, QuizGroupPermission

class AnswerInline(admin.TabularInline):
    """
    Widok inline dla odpowiedzi wewnątrz formularza pytania.
    
    Pozwala na dodawanie i edycję odpowiedzi bezpośrednio na stronie edycji pytania.
    """
    model = Answer
    extra = 2

class QuestionInline(admin.TabularInline):
    """
    Widok inline dla pytań wewnątrz formularza quizu.
    
    Umożliwia szybki podgląd pytań przypisanych do quizu.
    """
    model = Question
    extra = 1
    show_change_link = True

class QuizUserPermissionInline(admin.TabularInline):
    """
    Widok inline dla uprawnień użytkowników wewnątrz formularza quizu.
    
    Umożliwia przypisywanie ról (VIEWER/EDITOR) konkretnym użytkownikom.
    """
    model = QuizUserPermission
    extra = 1
    autocomplete_fields = ['user']

class QuizGroupPermissionInline(admin.TabularInline):
    """
    Widok inline dla uprawnień grup wewnątrz formularza quizu.
    
    Umożliwia przypisywanie ról całym grupom użytkowników.
    """
    model = QuizGroupPermission
    extra = 1

@admin.register(Quiz)
class QuizAdmin(admin.ModelAdmin):
    """
    Konfiguracja panelu admina dla modelu Quiz.

    Zarządza wyświetlaniem, filtrowaniem i edycją quizów. Zawiera również
    formularze inline do zarządzania uprawnieniami i pytaniami.

    Attributes:
        list_display (tuple): Kolumny widoczne na liście quizów.
        list_filter (tuple): Filtry boczne (widoczność, autor).
        search_fields (tuple): Pola przeszukiwane (tytuł, nazwa autora).
        inlines (list): Lista klas inline dołączonych do widoku edycji.
    """
    list_display = ('title', 'author', 'visibility', 'time_limit')
    list_filter = ('visibility', 'author')
    search_fields = ('title', 'author__username')
    inlines = [QuizUserPermissionInline, QuizGroupPermissionInline, QuestionInline]

@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    """
    Konfiguracja panelu admina dla modelu Question.

    Umożliwia zarządzanie pytaniami i przypisanymi do nich odpowiedziami (AnswerInline).

    Attributes:
        list_display (tuple): Kolumny widoczne na liście pytań.
        inlines (list): Lista klas inline (odpowiedzi).
    """
    list_display = ('text', 'quiz', 'question_type')
    inlines = [AnswerInline]

@admin.register(QuizGroup)
class QuizGroupAdmin(admin.ModelAdmin):
    """
    Konfiguracja panelu admina dla modelu QuizGroup.

    Attributes:
        filter_horizontal (tuple): Używa wygodnego widgetu JS do wybierania wielu użytkowników.
    """
    filter_horizontal = ('members',)

admin.site.register(QuizAttempt)