# quizzes/views.py
import json
import requests
import random
import os
from dotenv import load_dotenv

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse, HttpRequest
from django.utils.text import slugify
from django.db import transaction
from django.core.exceptions import ValidationError, PermissionDenied
from django.views.decorators.http import require_POST
from django.contrib.auth import get_user_model
from django.db.models import Q

from .models import Quiz, Question, Answer, QuizAttempt, QuizGroup, QuizUserPermission, QuizGroupPermission
from .forms import (
    QuizForm, QuestionForm, AnswerFormSet, QuizGenerationForm, QuizGroupForm,
    QuizUserPermissionFormSet, QuizGroupPermissionFormSet
)

User = get_user_model()
load_dotenv()

HF_TOKEN = os.getenv("HF_TOKEN")
HF_API_URL = "https://router.huggingface.co/v1/chat/completions"

def home_view(request: HttpRequest) -> HttpResponse:
    """
    Widok strony głównej aplikacji.

    Wyświetla listę publicznych quizów. Obsługuje również wyszukiwanie quizów po tytule.
    Wyniki są ograniczone do 10 najnowszych quizów.

    Args:
        request (HttpRequest): Obiekt żądania HTTP. Parametr GET 'q' służy do wyszukiwania.

    Returns:
        HttpResponse: Wyrenderowany szablon 'home.html' z listą quizów.
    """
    query = request.GET.get('q', '')
    
    # Pobieramy publiczne quizy, filtrujemy po tytule (jesli jest zapytanie),
    # sortujemy od najnowszych (-id) i bierzemy tylko pierwsze 10.
    quizzes = Quiz.objects.filter(
        visibility='PUBLIC', 
        title__icontains=query
    ).order_by('-id')[:10]
    
    return render(request, 'home.html', {
        'quizzes': quizzes,
        'query': query
    })

def _can_view_quiz(user, quiz) -> bool:
    """
    Pomocnicza funkcja sprawdzająca uprawnienia do podglądu quizu.

    Args:
        user (User): Użytkownik próbujący uzyskać dostęp.
        quiz (Quiz): Quiz, do którego użytkownik chce uzyskać dostęp.

    Returns:
        bool: True, jeśli użytkownik ma dostęp, False w przeciwnym razie.
    """
    return quiz.can_view(user)

def _check_edit_permission(user, quiz):
    """
    Sprawdza uprawnienia do edycji quizu i rzuca wyjątek w przypadku ich braku.

    Args:
        user (User): Użytkownik próbujący edytować quiz.
        quiz (Quiz): Edytowany quiz.

    Raises:
        PermissionDenied: Jeśli użytkownik nie ma uprawnień edytora ani autora.
    """
    if not quiz.can_edit(user):
        raise PermissionDenied("Nie masz uprawnień do edycji tego quizu.")

@login_required
def group_list_view(request: HttpRequest) -> HttpResponse:
    """
    Wyświetla listę grup użytkowników stworzonych przez zalogowanego użytkownika.

    Args:
        request (HttpRequest): Obiekt żądania HTTP.

    Returns:
        HttpResponse: Wyrenderowany szablon 'quizzes/group_list.html'.
    """
    groups = QuizGroup.objects.filter(owner=request.user)
    return render(request, 'quizzes/group_list.html', {'groups': groups})

@login_required
def group_create_view(request: HttpRequest) -> HttpResponse:
    """
    Tworzy nową grupę użytkowników.

    Obsługuje formularz tworzenia grupy. Właściciel grupy jest ustawiany automatycznie
    na zalogowanego użytkownika.

    Args:
        request (HttpRequest): Obiekt żądania HTTP.

    Returns:
        HttpResponse: Wyrenderowany formularz lub przekierowanie do listy grup po sukcesie.
    """
    if request.method == 'POST':
        form = QuizGroupForm(request.POST)
        form.fields['members'].queryset = User.objects.exclude(pk=request.user.pk)
        
        if form.is_valid():
            group = form.save(commit=False)
            group.owner = request.user
            group.save()
            form.save_m2m()
            messages.success(request, f"Grupa '{group.name}' została utworzona.")
            return redirect('group-list')
    else:
        form = QuizGroupForm()
        form.fields['members'].queryset = User.objects.exclude(pk=request.user.pk)
    
    return render(request, 'quizzes/group_form.html', {'form': form, 'title': 'Nowa grupa'})

@login_required
def group_edit_view(request: HttpRequest, pk: int) -> HttpResponse:
    """
    Edytuje istniejącą grupę użytkowników.

    Tylko właściciel grupy może ją edytować.

    Args:
        request (HttpRequest): Obiekt żądania HTTP.
        pk (int): Klucz główny edytowanej grupy.

    Returns:
        HttpResponse: Wyrenderowany formularz edycji lub przekierowanie po zapisie.
    """
    group = get_object_or_404(QuizGroup, pk=pk, owner=request.user)
    
    if request.method == 'POST':
        form = QuizGroupForm(request.POST, instance=group)
        form.fields['members'].queryset = User.objects.exclude(pk=request.user.pk)
        
        if form.is_valid():
            form.save()
            messages.success(request, "Zaktualizowano grupę.")
            return redirect('group-list')
    else:
        form = QuizGroupForm(instance=group)
        form.fields['members'].queryset = User.objects.exclude(pk=request.user.pk)
        
    return render(request, 'quizzes/group_form.html', {'form': form, 'title': f'Edycja grupy: {group.name}'})

@login_required
def group_delete_view(request: HttpRequest, pk: int) -> HttpResponse:
    """
    Usuwa grupę użytkowników.

    Wymaga potwierdzenia metodą POST. Tylko właściciel grupy może ją usunąć.

    Args:
        request (HttpRequest): Obiekt żądania HTTP.
        pk (int): Klucz główny usuwanej grupy.

    Returns:
        HttpResponse: Strona potwierdzenia usunięcia lub przekierowanie po usunięciu.
    """
    group = get_object_or_404(QuizGroup, pk=pk, owner=request.user)
    if request.method == 'POST':
        group.delete()
        messages.success(request, "Grupa została usunięta.")
        return redirect('group-list')
    return render(request, 'quizzes/group_confirm_delete.html', {'group': group})

def quiz_detail_view(request: HttpRequest, pk: int) -> HttpResponse:
    """
    Wyświetla szczegóły quizu (strona startowa przed rozpoczęciem).

    Sprawdza uprawnienia użytkownika do podglądu quizu (autor, edytor, viewer, publiczny).

    Args:
        request (HttpRequest): Obiekt żądania HTTP.
        pk (int): Klucz główny quizu.

    Returns:
        HttpResponse: Szablon ze szczegółami quizu lub przekierowanie w przypadku braku uprawnień.
    """
    quiz = get_object_or_404(Quiz, pk=pk)
    if quiz.can_view(request.user):
        return render(request, 'quizzes/quiz_detail.html', {'quiz': quiz})
    
    messages.error(request, "Nie masz uprawnień do wyświetlenia tego quizu.")
    return redirect('home')

@login_required
def my_quizzes_view(request: HttpRequest) -> HttpResponse:
    """
    Wyświetla pulpit nawigacyjny z quizami użytkownika.

    Quizy są podzielone na trzy kategorie:
    1. Utworzone przez użytkownika (Autor).
    2. Udostępnione do edycji (Edytor).
    3. Udostępnione do rozwiązania (Przeglądający/Viewer).

    Args:
        request (HttpRequest): Obiekt żądania HTTP.

    Returns:
        HttpResponse: Wyrenderowany szablon 'quizzes/my_quizzes.html'.
    """
    # 1. Quizy autorskie
    created_quizzes = Quiz.objects.filter(author=request.user)
    
    # Pobierz grupy użytkownika dla zoptymalizowanych zapytań
    user_groups = request.user.group_memberships.all()

    # 2. Quizy, w których jestem edytorem (bezpośrednio LUB przez grupę z rolą EDITOR)
    # Wykluczamy te, których jestem autorem
    editable_quizzes = Quiz.objects.filter(
        Q(quizuserpermission__user=request.user, quizuserpermission__role='EDITOR') |
        Q(quizgrouppermission__group__in=user_groups, quizgrouppermission__role='EDITOR')
    ).exclude(author=request.user).distinct()

    # 3. Quizy tylko do odczytu
    # Wykluczamy te, które już są w created lub editable
    shared_quizzes = Quiz.objects.filter(
        Q(quizuserpermission__user=request.user) | 
        Q(quizgrouppermission__group__in=user_groups)
    ).exclude(pk__in=created_quizzes).exclude(pk__in=editable_quizzes).distinct()
    
    return render(request, 'quizzes/my_quizzes.html', {
        'quizzes': created_quizzes,
        'editable_quizzes': editable_quizzes,
        'shared_quizzes': shared_quizzes
    })

@login_required
def quiz_create_view(request: HttpRequest) -> HttpResponse:
    """
    Tworzy nowy quiz wraz z uprawnieniami dla użytkowników i grup.

    Wykorzystuje transakcję atomową do spójnego zapisu quizu oraz formsetów uprawnień.

    Args:
        request (HttpRequest): Obiekt żądania HTTP.

    Returns:
        HttpResponse: Formularz tworzenia quizu lub przekierowanie do edycji po utworzeniu.
    """
    if request.method == 'POST':
        form = QuizForm(request.POST)
        user_perms_formset = QuizUserPermissionFormSet(request.POST, prefix='users')
        group_perms_formset = QuizGroupPermissionFormSet(request.POST, prefix='groups')
        
        if form.is_valid() and user_perms_formset.is_valid() and group_perms_formset.is_valid():
            with transaction.atomic():
                quiz = form.save(commit=False)
                quiz.author = request.user
                quiz.save()
                
                # Zapisujemy uprawnienia (Formsety)
                user_perms_formset.instance = quiz
                user_perms_formset.save()
                
                group_perms_formset.instance = quiz
                group_perms_formset.save()
                
            messages.success(request, f"Quiz '{quiz.title}' został utworzony.")
            return redirect('quiz-edit', pk=quiz.pk)
    else:
        form = QuizForm()
        user_perms_formset = QuizUserPermissionFormSet(prefix='users')
        group_perms_formset = QuizGroupPermissionFormSet(prefix='groups')

    return render(request, 'quizzes/quiz_form.html', {
        'quiz_form': form,
        'user_perms_formset': user_perms_formset,
        'group_perms_formset': group_perms_formset,
        'is_new': True
    })

@login_required
def quiz_edit_view(request: HttpRequest, pk: int) -> HttpResponse:
    """
    Edytuje istniejący quiz oraz jego ustawienia uprawnień.

    Sprawdza uprawnienia edytora przed wykonaniem akcji.

    Args:
        request (HttpRequest): Obiekt żądania HTTP.
        pk (int): Klucz główny edytowanego quizu.

    Returns:
        HttpResponse: Formularz edycji quizu.
    """
    quiz = get_object_or_404(Quiz, pk=pk)
    _check_edit_permission(request.user, quiz)
    
    if request.method == 'POST':
        form = QuizForm(request.POST, instance=quiz)
        user_perms_formset = QuizUserPermissionFormSet(request.POST, instance=quiz, prefix='users')
        group_perms_formset = QuizGroupPermissionFormSet(request.POST, instance=quiz, prefix='groups')
        
        if form.is_valid() and user_perms_formset.is_valid() and group_perms_formset.is_valid():
            with transaction.atomic():
                form.save()
                user_perms_formset.save()
                group_perms_formset.save()
                
            messages.success(request, "Zapisano zmiany w quizie.")
            return redirect('quiz-edit', pk=quiz.pk)
    else:
        form = QuizForm(instance=quiz)
        user_perms_formset = QuizUserPermissionFormSet(instance=quiz, prefix='users')
        group_perms_formset = QuizGroupPermissionFormSet(instance=quiz, prefix='groups')
    
    return render(request, 'quizzes/quiz_form.html', {
        'quiz_form': form,
        'user_perms_formset': user_perms_formset,
        'group_perms_formset': group_perms_formset,
        'quiz': quiz
    })

@login_required
def quiz_generate_view(request: HttpRequest) -> HttpResponse:
    """
    Generuje quiz automatycznie przy użyciu sztucznej inteligencji (HuggingFace API).

    Wysyła zapytanie do modelu LLM (np. Llama 3) z prośbą o wygenerowanie pytań
    w formacie JSON, parsuje odpowiedź i tworzy strukturę quizu w bazie danych.

    Args:
        request (HttpRequest): Obiekt żądania HTTP.

    Returns:
        HttpResponse: Formularz generatora lub przekierowanie do edycji wygenerowanego quizu.
    """
    if request.method == 'POST':
        form = QuizGenerationForm(request.POST)
        if form.is_valid():
            topic = form.cleaned_data['topic']
            count = form.cleaned_data['count']
            
            try:
                if not HF_TOKEN:
                    raise ValueError("Brak klucza API (HF_TOKEN) w pliku .env")

                headers = {
                    "Authorization": f"Bearer {HF_TOKEN}",
                    "Content-Type": "application/json"
                }
                
                system_message = (
                    "Jesteś ekspertem tworzącym quizy edukacyjne. "
                    "Twoim zadaniem jest generowanie pytań w formacie czystego JSON. "
                    "Nie dodawaj żadnych wstępów, wyjaśnień ani formatowania Markdown (np. ```json). "
                    "Zwróć TYLKO obiekt JSON."
                )
                
                user_prompt = f"""
                Stwórz quiz w języku polskim na temat: "{topic}".
                Liczba pytań: {count}.
                
                Wymagana struktura JSON:
                {{
                    "questions": [
                        {{
                            "question": "Treść pytania?",
                            "answers": ["Odp A", "Odp B", "Odp C", "Odp D"],
                            "correct_index": 0
                        }}
                    ]
                }}
                Ważne:
                1. "correct_index" to numer poprawnej odpowiedzi (0-3).
                2. Wygeneruj dokładnie {count} pytań.
                """

                payload = {
                    "model": "meta-llama/Meta-Llama-3-8B-Instruct", 
                    "messages": [
                        {"role": "system", "content": system_message},
                        {"role": "user", "content": user_prompt}
                    ],
                    "max_tokens": 2048,
                    "stream": False,
                    "temperature": 0.7
                }

                response = requests.post(HF_API_URL, headers=headers, json=payload)
                
                if response.status_code != 200:
                    try:
                        err_msg = response.json().get('error', response.text)
                    except:
                        err_msg = response.text
                    raise Exception(f"Błąd API ({response.status_code}): {err_msg}")

                result = response.json()
                
                if 'choices' in result and len(result['choices']) > 0:
                    generated_text = result['choices'][0]['message']['content'].strip()
                else:
                    raise ValueError(f"Pusta odpowiedź od modelu: {result}")
                
                if "```json" in generated_text:
                    generated_text = generated_text.split("```json")[1].split("```")[0].strip()
                elif "```" in generated_text:
                    generated_text = generated_text.split("```")[1].strip()

                try:
                    data = json.loads(generated_text)
                except json.JSONDecodeError:
                    if generated_text.rfind('}') != -1:
                        fixed_text = generated_text[:generated_text.rfind('}')+1] + "]}"
                        try:
                            data = json.loads(fixed_text)
                        except:
                            raise ValueError("Otrzymano niepoprawny JSON od AI.")
                    else:
                        raise ValueError("Otrzymano niepoprawny JSON od AI.")

                questions_list = data.get('questions', [])

                if not questions_list:
                    raise ValueError("Lista pytań jest pusta.")

                with transaction.atomic():
                    new_quiz = Quiz.objects.create(
                        title=f"AI Quiz: {topic}",
                        author=request.user,
                        visibility='PRIVATE'
                    )
                    
                    for item in questions_list:
                        q_text = item.get('question')
                        answers = item.get('answers', [])
                        correct_idx = item.get('correct_index', 0)
                        
                        if q_text and isinstance(answers, list) and len(answers) >= 2:
                            if not isinstance(correct_idx, int) or correct_idx < 0 or correct_idx >= len(answers):
                                correct_idx = 0
                            
                            q_obj = Question.objects.create(
                                quiz=new_quiz,
                                text=q_text,
                                question_type=Question.QuestionType.SINGLE
                            )
                            
                            for i, ans_text in enumerate(answers):
                                Answer.objects.create(
                                    question=q_obj,
                                    text=str(ans_text),
                                    is_correct=(i == correct_idx)
                                )

                messages.success(request, f"Sukces! Wygenerowano quiz z {len(questions_list)} pytaniami.")
                return redirect('quiz-edit', pk=new_quiz.pk)

            except Exception as e:
                print(f"DEBUG ERROR: {str(e)}")
                messages.error(request, f"Wystąpił błąd: {str(e)}")
                
    else:
        form = QuizGenerationForm()

    return render(request, 'quizzes/quiz_generate.html', {'form': form})

@login_required
def question_create_view(request: HttpRequest, quiz_pk: int) -> HttpResponse:
    """
    Dodaje nowe pytanie do quizu.

    Wyświetla formularz pytania oraz formset dla odpowiedzi.
    Waliduje poprawność logiczną (np. czy jest poprawna odpowiedź dla SINGLE choice).

    Args:
        request (HttpRequest): Obiekt żądania HTTP.
        quiz_pk (int): Klucz główny quizu, do którego dodawane jest pytanie.

    Returns:
        HttpResponse: Formularz dodawania pytania lub przekierowanie po zapisie.
    """
    quiz = get_object_or_404(Quiz, pk=quiz_pk)
    _check_edit_permission(request.user, quiz)
    
    if request.method == 'POST':
        question_form = QuestionForm(request.POST)
        answer_formset = AnswerFormSet(request.POST)
        
        if question_form.is_valid() and answer_formset.is_valid():
            question_type = question_form.cleaned_data.get('question_type')
            correct_answers_count = 0
            for form in answer_formset.cleaned_data:
                if form.get('is_correct'):
                    correct_answers_count += 1
            
            if question_type == Question.QuestionType.SINGLE and correct_answers_count != 1:
                question_form.add_error('question_type', 'Pytanie jednokrotnego wyboru musi mieć dokładnie jedną poprawną odpowiedź.')
            elif question_type == Question.QuestionType.MULTIPLE and correct_answers_count == 0:
                question_form.add_error('question_type', 'Pytanie wielokrotnego wyboru musi mieć przynajmniej jedną poprawną odpowiedź.')
            else:
                question = question_form.save(commit=False)
                question.quiz = quiz
                question.save()
                answer_formset.instance = question
                answer_formset.save()
                messages.success(request, "Nowe pytanie zostało dodane.")
                return redirect('quiz-edit', pk=quiz.pk)
    else:
        question_form = QuestionForm()
        answer_formset = AnswerFormSet()
    
    context = {
        'question_form': question_form,
        'answer_formset': answer_formset,
        'quiz': quiz
    }
    return render(request, 'quizzes/question_form.html', context)

@login_required
def question_edit_view(request: HttpRequest, pk: int) -> HttpResponse:
    """
    Edytuje istniejące pytanie i jego odpowiedzi.

    Args:
        request (HttpRequest): Obiekt żądania HTTP.
        pk (int): Klucz główny edytowanego pytania.

    Returns:
        HttpResponse: Formularz edycji pytania.
    """
    question = get_object_or_404(Question, pk=pk)
    _check_edit_permission(request.user, question.quiz)
    
    if request.method == 'POST':
        question_form = QuestionForm(request.POST, instance=question)
        answer_formset = AnswerFormSet(request.POST, instance=question)
        
        if question_form.is_valid() and answer_formset.is_valid():
            question_type = question_form.cleaned_data.get('question_type')
            correct_answers_count = 0
            for form in answer_formset.cleaned_data:
                if form.get('is_correct') and not form.get('DELETE'):
                    correct_answers_count += 1
            
            if question_type == Question.QuestionType.SINGLE and correct_answers_count != 1:
                question_form.add_error('question_type', 'Pytanie jednokrotnego wyboru musi mieć dokładnie jedną poprawną odpowiedź.')
            elif question_type == Question.QuestionType.MULTIPLE and correct_answers_count == 0:
                question_form.add_error('question_type', 'Pytanie wielokrotnego wyboru musi mieć przynajmniej jedną poprawną odpowiedź.')
            else:
                question_form.save()
                answer_formset.save()
                messages.success(request, "Pytanie zostało zaktualizowane.")
                return redirect('quiz-edit', pk=question.quiz.pk)
    else:
        question_form = QuestionForm(instance=question)
        answer_formset = AnswerFormSet(instance=question)
        
    context = {
        'question_form': question_form,
        'answer_formset': answer_formset,
        'quiz': question.quiz
    }
    return render(request, 'quizzes/question_form.html', context)

@login_required
def question_delete_view(request: HttpRequest, pk: int) -> HttpResponse:
    """
    Usuwa pytanie z quizu.

    Args:
        request (HttpRequest): Obiekt żądania HTTP.
        pk (int): Klucz główny usuwanego pytania.

    Returns:
        HttpResponse: Potwierdzenie usunięcia lub przekierowanie.
    """
    question = get_object_or_404(Question, pk=pk)
    _check_edit_permission(request.user, question.quiz)
    if request.method == 'POST':
        quiz_pk = question.quiz.pk
        question.delete()
        messages.success(request, "Pytanie zostało usunięte.")
        return redirect('quiz-edit', pk=quiz_pk)
    return render(request, 'quizzes/question_confirm_delete.html', {'question': question})

@login_required
def quiz_delete_view(request: HttpRequest, pk: int) -> HttpResponse:
    """
    Usuwa cały quiz.

    Operacja dozwolona tylko dla autora quizu.

    Args:
        request (HttpRequest): Obiekt żądania HTTP.
        pk (int): Klucz główny usuwanego quizu.

    Returns:
        HttpResponse: Potwierdzenie usunięcia lub przekierowanie do listy quizów.
    """
    # Usuwać quiz może tylko autor
    quiz = get_object_or_404(Quiz, pk=pk, author=request.user)
    if request.method == 'POST':
        quiz.delete()
        messages.success(request, "Quiz został usunięty.")
        return redirect('my-quizzes')
    return render(request, 'quizzes/quiz_confirm_delete.html', {'quiz': quiz})

def quiz_take_view(request: HttpRequest, pk: int) -> HttpResponse:
    """
    Obsługuje proces rozwiązywania quizu przez użytkownika.

    Metoda GET:
        Przygotowuje quiz, losuje pytania zgodnie z limitem `questions_count_limit`,
        miesza kolejność odpowiedzi i renderuje interfejs rozwiązywania.

    Metoda POST:
        Odbiera odpowiedzi użytkownika, oblicza wynik, zapisuje próbę (`QuizAttempt`)
        i wyświetla podsumowanie.

    Args:
        request (HttpRequest): Obiekt żądania HTTP.
        pk (int): Klucz główny rozwiązywanego quizu.

    Returns:
        HttpResponse: Widok rozwiązywania quizu lub widok wyników.
    """
    quiz = get_object_or_404(Quiz, pk=pk)

    if not _can_view_quiz(request.user, quiz):
        messages.error(request, "Nie masz uprawnień do wyświetlenia tego quizu.")
        return redirect('home')

    if quiz.questions.count() == 0:
        messages.info(request, "Ten quiz nie ma jeszcze pytań.")
        return redirect('quiz-detail', pk=quiz.pk)
    
    time_limit_seconds = quiz.time_limit * 60

    if request.method == 'POST':
        # --- LOGIKA ZAPISU WYNIKU (Bez zmian) ---
        # Pobieramy ID pytań, które faktycznie brały udział w losowaniu
        question_ids_str = request.POST.get('question_ids_included', '')
        
        questions_to_grade = []
        if question_ids_str:
            try:
                question_ids = [int(qid) for qid in question_ids_str.split(',') if qid.strip().isdigit()]
                questions_to_grade = quiz.questions.filter(id__in=question_ids).prefetch_related('answers')
            except ValueError:
                pass
        
        # Zabezpieczenie: jeśli lista jest pusta (błąd formularza), weź wszystkie (to powodowało błąd 50 pytań)
        if not questions_to_grade:
            questions_to_grade = quiz.questions.prefetch_related('answers')

        total = len(questions_to_grade) # ### Teraz total to np. 15, a nie 50
        correct_count = 0
        details = []

        for question in questions_to_grade:
            field = f"q_{question.id}"
            correct_ids = set(question.answers.filter(is_correct=True).values_list('id', flat=True))
            chosen_ids = set()
            
            # Pobieranie chosen_ids z request.POST (Twoja logika)...
            if question.question_type == 'SINGLE':
                 val = request.POST.get(field)
                 if val: chosen_ids.add(int(val))
            else:
                 vals = request.POST.getlist(field)
                 chosen_ids = {int(v) for v in vals}

            is_correct = (chosen_ids == correct_ids) and len(chosen_ids) > 0
            if is_correct:
                correct_count += 1
            
            details.append({
                'question': question,
                'answers': list(question.answers.all()), # Tu można dodać .order_by('?') jeśli chcesz mieszać odpowiedzi na ekranie wyniku
                'chosen_ids': chosen_ids,
                'correct_ids': correct_ids,
                'is_correct': is_correct,
            })

        # Obliczanie wyniku
        score_percent = round((correct_count / total) * 100) if total > 0 else 0
        time_over_bool = request.POST.get('time_over') == '1'

        user_to_save = request.user if request.user.is_authenticated else None
        
        QuizAttempt.objects.create(
            quiz=quiz,
            user=user_to_save,
            score=score_percent,
            correct_count=correct_count,
            total_questions=total,
            time_over=time_over_bool
        )

        return render(request, 'quizzes/quiz_result.html', {
            'quiz': quiz,
            'total': total,
            'correct_count': correct_count,
            'score_percent': score_percent,
            'details': details,
            'time_over': time_over_bool
        })
    
    else:
        # Pobieramy wszystkie pytania
        all_questions = list(quiz.questions.prefetch_related('answers'))
        random.shuffle(all_questions) # Mieszamy pulę

        # ### ZASTOSOWANIE LIMITU ###
        limit = quiz.questions_count_limit
        if limit > 0 and limit < len(all_questions):
            selected_questions = all_questions[:limit]
        else:
            selected_questions = all_questions

        # ### GENEROWANIE STRINGA ID ###
        # To jest kluczowe dla template'u - tworzymy string np. "10,4,22"
        selected_ids_str = ",".join(str(q.id) for q in selected_questions)

        # Przygotowanie JSON dla JS
        questions_json = []
        for q in selected_questions:
            answers = list(q.answers.all())
            random.shuffle(answers)
            answers_data = [{'id': a.id, 'text': a.text, 'is_correct': a.is_correct} for a in answers]
            questions_json.append({
                'id': q.id,
                'text': q.text,
                'type': q.question_type,
                'answers': answers_data
            })

        import json
        questions_json_str = json.dumps(questions_json)
        
        time_limit_seconds = quiz.time_limit * 60

        return render(request, 'quizzes/quiz_take.html', {
            'quiz': quiz,
            'questions_json': questions_json_str,
            'time_limit': time_limit_seconds,
            'instant_feedback': quiz.instant_feedback,
            'selected_ids_str': selected_ids_str, # ### PRZEKAZANIE DO SZABLONU ###
        })

@login_required
def quiz_export_json_view(request: HttpRequest, pk: int) -> HttpResponse:
    """
    Eksportuje quiz do pliku JSON.

    Pobiera strukturę quizu (pytania, odpowiedzi) i zwraca jako plik
    do pobrania (Content-Disposition attachment).

    Args:
        request (HttpRequest): Obiekt żądania HTTP.
        pk (int): Klucz główny eksportowanego quizu.

    Returns:
        HttpResponse: Odpowiedź zawierająca plik JSON.
    """
    quiz = get_object_or_404(Quiz, pk=pk)
    _check_edit_permission(request.user, quiz)

    questions_data = []
    for q in quiz.questions.prefetch_related('answers'):
        answers_data = [
            {'text': ans.text, 'is_correct': ans.is_correct}
            for ans in q.answers.all()
        ]
        questions_data.append({
            'text': q.text,
            'explanation': q.explanation,
            'question_type': q.question_type,
            'answers': answers_data
        })
    json_data = {'title': quiz.title, 'questions': questions_data}
    response = HttpResponse(
        json.dumps(json_data, indent=4, ensure_ascii=False),
        content_type='application/json; charset=utf-8'
    )
    safe_title = slugify(quiz.title) or 'quiz'
    response['Content-Disposition'] = f'attachment; filename="quiz_{quiz.pk}_{safe_title}.json"'
    return response

@login_required
@require_POST
@transaction.atomic
def quiz_import_json_view(request: HttpRequest, pk: int) -> HttpResponse:
    """
    Importuje pytania do quizu z pliku JSON.

    Parsuje przesłany plik, waliduje strukturę danych i tworzy obiekty pytań/odpowiedzi w bazie.
    Obsługuje transakcyjność - w razie błędu żadne zmiany nie są zapisywane.

    Args:
        request (HttpRequest): Obiekt żądania HTTP (musi zawierać plik 'json_file').
        pk (int): Klucz główny quizu, do którego importujemy pytania.

    Returns:
        HttpResponse: Przekierowanie do edycji quizu z komunikatem sukcesu lub błędu.
    """
    quiz = get_object_or_404(Quiz, pk=pk)
    _check_edit_permission(request.user, quiz)
    
    if 'json_file' not in request.FILES:
        messages.error(request, "Nie wybrano pliku.")
        return redirect('quiz-edit', pk=quiz.pk)

    file = request.FILES['json_file']

    if not file.name.endswith('.json'):
        messages.error(request, "Plik musi być w formacie .json.")
        return redirect('quiz-edit', pk=quiz.pk)

    try:
        try:
            file_content = file.read().decode('utf-8')
            data = json.loads(file_content)
        except UnicodeDecodeError:
            raise ValidationError("Plik ma niepoprawne kodowanie. Wymagane jest UTF-8.")
        except json.JSONDecodeError:
            raise ValidationError("Błąd parsowania pliku JSON. Upewnij się, że plik jest poprawny.")

        if 'questions' not in data or not isinstance(data['questions'], list):
            raise ValidationError("Plik JSON musi zawierać klucz 'questions' z listą pytań.")

        questions_to_create = [] 

        for i, q_data in enumerate(data['questions']):
            q_num = i + 1
            
            if not isinstance(q_data, dict):
                raise ValidationError(f"Pytanie {q_num}: Nie jest poprawnym obiektem JSON.")
                
            text = q_data.get('text')
            if not text or not isinstance(text, str):
                raise ValidationError(f"Pytanie {q_num}: Brak lub niepoprawny klucz 'text'.")

            question_type = q_data.get('question_type', Question.QuestionType.SINGLE)
            
            explanation = q_data.get('explanation', '')
            answers_data = q_data.get('answers')
            
            if not answers_data or not isinstance(answers_data, list) or len(answers_data) < 2:
                 raise ValidationError(f"Pytanie {q_num}: Musi zawierać listę 'answers' z co najmniej 2 odpowiedziami.")

            validated_answers = []
            
            # Zliczymy poprawne odpowiedzi dla tego pytania
            correct_count = 0 
            
            for j, ans_data in enumerate(answers_data):
                ans_num = j + 1
                if not isinstance(ans_data, dict):
                     raise ValidationError(f"Pytanie {q_num}, Odpowiedź {ans_num}: Błędny format.")
                
                ans_text = ans_data.get('text')
                is_correct = ans_data.get('is_correct', False) # Domyślnie False
                
                if not ans_text:
                    continue
                
                if is_correct:
                    correct_count += 1

                validated_answers.append({'text': ans_text, 'is_correct': is_correct})

            # --- DODANA WALIDACJA LOGICZNA ---
            if question_type == 'SINGLE':
                if correct_count != 1:
                    raise ValidationError(
                        f"Pytanie {q_num} ('{text[:30]}...'): Typ 'Jednokrotny wybór' musi mieć dokładnie 1 poprawną odpowiedź (znaleziono {correct_count})."
                    )
            elif question_type == 'MULTIPLE':
                if correct_count < 1:
                    raise ValidationError(
                        f"Pytanie {q_num} ('{text[:30]}...'): Typ 'Wielokrotny wybór' musi mieć przynajmniej 1 poprawną odpowiedź."
                    )
            # ---------------------------------
            
            questions_to_create.append({
                'q_obj': Question(quiz=quiz, text=text, explanation=explanation, question_type=question_type),
                'answers': validated_answers
            })
        
        for q_batch in questions_to_create:
            q = q_batch['q_obj']
            q.save() 
            
            answers_to_save = [
                Answer(question=q, text=ans_data['text'], is_correct=ans_data['is_correct'])
                for ans_data in q_batch['answers']
            ]
            Answer.objects.bulk_create(answers_to_save)
        
        messages.success(request, f"Pomyślnie zaimportowano pytania.")

    except ValidationError as e:
        messages.error(request, f"Błąd walidacji: {e.message}")
    except Exception as e:
        messages.error(request, f"Wystąpił nieoczekiwany błąd: {e}")

    return redirect('quiz-edit', pk=quiz.pk)