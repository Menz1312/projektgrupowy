# quizzes/forms.py
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
        # 🔽 ZMIANA: Dodaj 'question_type' do pól
        fields = ['text', 'explanation', 'question_type']
        widgets = {
            'text': forms.Textarea(attrs={'rows': 3}),
            'explanation': forms.Textarea(attrs={
                'rows': 3,
                'placeholder': 'Opcjonalnie: wytłumacz poprawną odpowiedź / dodaj źródło'
            }),
            # 🔽 NOWY WIDOK: (Opcjonalnie) Użyj RadioSelect zamiast domyślnego dropdown
            'question_type': forms.RadioSelect, 
        }
        labels = {
            'text': 'Treść pytania',
            'explanation': 'Objaśnienie (opcjonalnie)',
            'question_type': 'Typ pytania', # 🔽 NOWA ETYKIETA
        }

AnswerFormSet = inlineformset_factory(
    Question,
    Answer,
    fields=('text', 'is_correct'),
    extra=4,
    max_num=4,
    can_delete=False,
    labels={
        'text': 'Treść odpowiedzi',
        'is_correct': 'Czy ta odpowiedź jest poprawna?'
    },
    widgets = {
        'text': forms.TextInput(attrs={'placeholder': 'Wpisz odpowiedź...'}),
    }
)