# quizzes/forms.py
from django import forms
from .models import Quiz, Question, Answer
from django.forms import inlineformset_factory
from django.contrib.auth import get_user_model # <-- NOWY IMPORT

User = get_user_model() # <-- Pobranie modelu użytkownika

class QuizForm(forms.ModelForm):
    # --- NOWE POLE FORMULARZA ---
    # Definiujemy je jawnie, aby dostosować widget i queryset
    shared_with = forms.ModelMultipleChoiceField(
        queryset=User.objects.none(), # Zaczynamy od pustego QuerySet, widok je ustawi
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label="Udostępnij użytkownikom"
    )
    # --------------------------

    class Meta:
        model = Quiz
        # --- ZMODYFIKOWANE POLA ---
        fields = ['title', 'visibility', 'time_limit', 'shared_with']
        labels = {
            'title': 'Tytuł Quizu',
            'visibility': 'Widoczność',
            # 'time_limit' i 'shared_with' użyją etykiet z definicji
        }
        widgets = {
            'time_limit': forms.NumberInput(attrs={'min': 0, 'step': 1}),
            'visibility': forms.RadioSelect, # Lepsze niż <select>
        }

# (Reszta pliku - QuestionForm i AnswerFormSet - bez zmian)
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