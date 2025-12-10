# quizzes/forms.py
from django import forms
from .models import Quiz, Question, Answer, QuizGroup, QuizUserPermission, QuizGroupPermission
from django.forms import inlineformset_factory
from django.contrib.auth import get_user_model

User = get_user_model()

class QuizGroupForm(forms.ModelForm):
    """
    Formularz do tworzenia i edycji grup użytkowników.

    Pozwala wybrać nazwę grupy oraz jej członków spośród zarejestrowanych użytkowników.

    Attributes:
        members (ModelMultipleChoiceField): Pole wyboru wielokrotnego (checkboxy) z listą użytkowników.
    """
    members = forms.ModelMultipleChoiceField(
        queryset=User.objects.none(), 
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label="Wybierz członków grupy"
    )

    class Meta:
        model = QuizGroup
        fields = ['name', 'members']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'np. Klasa 3B'}),
        }

class QuizForm(forms.ModelForm):
    """
    Główny formularz konfiguracji Quizu.

    Obsługuje podstawowe ustawienia quizu takie jak tytuł, widoczność, limity czasu
    oraz tryb natychmiastowego sprawdzania.

    Pola formularza:
        - title: Tytuł quizu.
        - visibility: Radio button (Publiczny/Prywatny).
        - time_limit: Czas w minutach.
        - questions_count_limit: Limit pytań w jednym podejściu.
        - instant_feedback: Checkbox trybu natychmiastowego.
    """
    class Meta:
        model = Quiz
        fields = ['title', 'visibility', 'time_limit', 'questions_count_limit', 'instant_feedback']
        
        labels = {
            'title': 'Tytuł Quizu',
            'visibility': 'Widoczność',
        }
        widgets = {
            'time_limit': forms.NumberInput(attrs={'min': 0, 'step': 1}),
            'questions_count_limit': forms.NumberInput(attrs={'min': 1, 'max': 30, 'step': 1}),
            'visibility': forms.RadioSelect,
        }

# --- FORMSETY DLA UPRAWNIEŃ ---

_QuizUserPermissionFormSet = inlineformset_factory(
    Quiz,
    QuizUserPermission,
    fields=('user', 'role'),
    extra=1,
    can_delete=True,
    widgets={
        'user': forms.Select(attrs={'class': 'form-select'}),
        'role': forms.Select(attrs={'class': 'form-select'}),
    }
)

class QuizUserPermissionFormSet(_QuizUserPermissionFormSet):
    """
    Formset zarządzający przypisaniem uprawnień poszczególnych użytkowników do quizu.

    Jest to klasa rozszerzająca standardowy `inlineformset_factory`, która zarządza relacją
    między modelem `Quiz` a modelem pośrednim `QuizUserPermission`.

    **Kluczowe funkcje:**

    * Umożliwia dodawanie, edycję i usuwanie wielu uprawnień w jednym żądaniu POST.
    * Zawiera pola:
        * `user`: Wybór użytkownika z listy.
        * `role`: Przypisanie roli (np. 'VIEWER' lub 'EDITOR').
    * Obsługuje flagę `DELETE` do usuwania istniejących uprawnień.
    """
    pass

_QuizGroupPermissionFormSet = inlineformset_factory(
    Quiz,
    QuizGroupPermission,
    fields=('group', 'role'),
    extra=1,
    can_delete=True,
    widgets={
        'group': forms.Select(attrs={'class': 'form-select'}),
        'role': forms.Select(attrs={'class': 'form-select'}),
    }
)

class QuizGroupPermissionFormSet(_QuizGroupPermissionFormSet):
    """
    Formset zarządzający przypisaniem uprawnień całych grup użytkowników do quizu.

    Działa analogicznie do `QuizUserPermissionFormSet`, ale operuje na modelu `QuizGroup`.
    Pozwala jednym kliknięciem nadać uprawnienia wszystkim członkom danej grupy.
    """
    pass

class QuestionForm(forms.ModelForm):
    """
    Formularz edycji treści pytania.

    Obsługuje treść pytania, opcjonalne wyjaśnienie oraz typ pytania
    (jednokrotny/wielokrotny wybór).
    """
    class Meta:
        model = Question
        fields = ['text', 'explanation', 'question_type']
        widgets = {
            'text': forms.Textarea(attrs={'rows': 3}),
            'explanation': forms.Textarea(attrs={
                'rows': 3,
                'placeholder': 'Opcjonalnie: wytłumacz poprawną odpowiedź / dodaj źródło'
            }),
            'question_type': forms.RadioSelect,
        }
        labels = {
            'text': 'Treść pytania',
            'explanation': 'Objaśnienie (opcjonalnie)',
            'question_type': 'Typ pytania',
        }

AnswerFormSet = inlineformset_factory(
    Question,
    Answer,
    fields=('text', 'is_correct'),
    extra=2, 
    max_num=10, 
    min_num=2, 
    can_delete=True, 
    labels={
        'text': 'Treść odpowiedzi',
        'is_correct': 'Czy ta odpowiedź jest poprawna?'
    },
    widgets = {
        'text': forms.TextInput(attrs={'placeholder': 'Wpisz odpowiedź...'}),
    }
)
AnswerFormSet.__doc__ = """
Formset do zarządzania odpowiedziami wewnątrz formularza pytania.
Wymusza minimum 2 odpowiedzi, pozwala na maksymalnie 10.
"""

class QuizGenerationForm(forms.Form):
    """
    Prosty formularz niepowiązany z modelem (Unbound Form) do obsługi generatora AI.

    Służy do pobrania tematu i liczby pytań od użytkownika, które następnie
    są przekazywane do API HuggingFace.

    Attributes:
        topic (CharField): Temat quizu wprowadzany przez użytkownika.
        count (IntegerField): Oczekiwana liczba pytań (1-10).
    """
    topic = forms.CharField(
        label="Temat quizu", 
        max_length=100, 
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'np. Historia Polski, Programowanie w Pythonie...'})
    )
    count = forms.IntegerField(
        label="Liczba pytań", 
        min_value=1, 
        max_value=10, 
        initial=5,
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )