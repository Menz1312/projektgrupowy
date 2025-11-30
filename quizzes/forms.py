# quizzes/forms.py
from django import forms
from .models import Quiz, Question, Answer, QuizGroup
from django.forms import inlineformset_factory
from django.contrib.auth import get_user_model

User = get_user_model()

class QuizGroupForm(forms.ModelForm):
    members = forms.ModelMultipleChoiceField(
        queryset=User.objects.none(), # Zostanie nadpisane w widoku
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
    shared_with = forms.ModelMultipleChoiceField(
        queryset=User.objects.none(),
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label="Udostępnij użytkownikom (pojedynczo)"
    )

    shared_groups = forms.ModelMultipleChoiceField(
        queryset=QuizGroup.objects.none(), # Zostanie nadpisane w widoku
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label="Udostępnij całym grupom"
    )

    class Meta:
        model = Quiz
        fields = ['title', 'visibility', 'time_limit', 'shared_groups', 'shared_with'] # Dodane shared_groups
        labels = {
            'title': 'Tytuł Quizu',
            'visibility': 'Widoczność',
        }
        widgets = {
            'time_limit': forms.NumberInput(attrs={'min': 0, 'step': 1}),
            'visibility': forms.RadioSelect,
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

# --- NOWY FORMULARZ DO GENEROWANIA ---
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