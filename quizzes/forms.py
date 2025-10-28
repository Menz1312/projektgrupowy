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
        fields = ['text']
        labels = {
            'text': 'Treść pytania'
        }
        widgets = {
            'text': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Wpisz treść pytania...'}),
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