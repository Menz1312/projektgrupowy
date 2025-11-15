from django import forms
from .models import Quiz, Question, Answer
from django.forms import inlineformset_factory

class QuizForm(forms.ModelForm):
    class Meta:
        model = Quiz
        fields = ['title', 'visibility']
        labels = {
            'title': 'Tytuł Quizu',
            'visibility': 'Widoczność'
        }

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
    
    # 1. Pokaż domyślnie 2 formularze (zamiast 4)
    extra=2, 
    
    # 2. Ustaw maksymalną liczbę na 10
    max_num=10, 
    
    # 3. Wymagaj co najmniej 2 odpowiedzi
    min_num=2, 
    
    # 4. Włącz możliwość usuwania
    can_delete=True, 
    
    labels={
        'text': 'Treść odpowiedzi',
        'is_correct': 'Czy ta odpowiedź jest poprawna?'
    },
    widgets = {
        'text': forms.TextInput(attrs={'placeholder': 'Wpisz odpowiedź...'}),
    }
)