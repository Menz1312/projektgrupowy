# quizzes/forms.py
from django import forms
from .models import Quiz, Question, Answer, QuizGroup, QuizUserPermission, QuizGroupPermission
from django.forms import inlineformset_factory
from django.contrib.auth import get_user_model

User = get_user_model()

class QuizGroupForm(forms.ModelForm):
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
    class Meta:
        model = Quiz
        # Dodaj 'instant_feedback' do listy poniżej:
        fields = ['title', 'visibility', 'time_limit', 'instant_feedback']
        
        labels = {
            'title': 'Tytuł Quizu',
            'visibility': 'Widoczność',
            # instant_feedback weźmie etykietę z modelu (verbose_name)
        }
        widgets = {
            'time_limit': forms.NumberInput(attrs={'min': 0, 'step': 1}),
            'visibility': forms.RadioSelect,
            # Dla pola BooleanField Django domyślnie wygeneruje Checkbox, co jest OK
        }

# --- FORMSETY DLA UPRAWNIEŃ ---

# Formularz dla pojedynczego wiersza uprawnień użytkownika
QuizUserPermissionFormSet = inlineformset_factory(
    Quiz,
    QuizUserPermission,
    fields=('user', 'role'),
    extra=1, # Ile pustych wierszy pokazać na start
    can_delete=True,
    widgets={
        'user': forms.Select(attrs={'class': 'form-select'}),
        'role': forms.Select(attrs={'class': 'form-select'}),
    }
)

# Formularz dla pojedynczego wiersza uprawnień grupy
QuizGroupPermissionFormSet = inlineformset_factory(
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

class QuestionForm(forms.ModelForm):
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

class QuizGenerationForm(forms.Form):
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