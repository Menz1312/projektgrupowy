# quizzes/forms.py
from django import forms
from .models import Quiz, Question, Answer
from django.forms import inlineformset_factory

class QuizForm(forms.ModelForm):
    class Meta:
        model = Quiz
        # --- ZMODYFIKOWANE POLA ---
        fields = ['title', 'visibility', 'time_limit']
        labels = {
            'title': 'Tytuł Quizu',
            'visibility': 'Widoczność',
            # 'time_limit' użyje verbose_name z modelu
        }
        # --- NOWY WIDGET ---
        widgets = {
            'time_limit': forms.NumberInput(attrs={'min': 0, 'step': 1})
        }

class QuestionForm(forms.ModelForm):
    # (reszta formularza QuestionForm bez zmian)
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

# (AnswerFormSet bez zmian)
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