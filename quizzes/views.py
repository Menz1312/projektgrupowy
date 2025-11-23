# quizzes/views.py
import json
import requests
import random
import os
from dotenv import load_dotenv  # <-- Nowy import

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse
from django.utils.text import slugify
from django.db import transaction
from django.core.exceptions import ValidationError
from django.views.decorators.http import require_POST
from django.contrib.auth import get_user_model

from .models import Quiz, Question, Answer, QuizAttempt
from .forms import QuizForm, QuestionForm, AnswerFormSet, QuizGenerationForm

User = get_user_model()

# Załaduj zmienne z pliku .env
load_dotenv()

# --- KONFIGURACJA HUGGING FACE ---
# Pobieramy token z bezpiecznego pliku .env
HF_TOKEN = os.getenv("HF_TOKEN")

# Nowy, uniwersalny endpoint routera (zgodny z OpenAI)
HF_API_URL = "https://router.huggingface.co/v1/chat/completions"

def home_view(request):
    query = request.GET.get('q', '')
    quizzes = Quiz.objects.filter(visibility='PUBLIC', title__icontains=query)
    return render(request, 'home.html', {'quizzes': quizzes})

def _can_view_quiz(user, quiz):
    if quiz.visibility == 'PUBLIC':
        return True
    if not user.is_authenticated:
        return False
    if quiz.author == user:
        return True
    if quiz.shared_with.filter(pk=user.pk).exists():
        return True
    return False

def quiz_detail_view(request, pk):
    quiz = get_object_or_404(Quiz, pk=pk)
    if _can_view_quiz(request.user, quiz):
        return render(request, 'quizzes/quiz_detail.html', {'quiz': quiz})
    
    messages.error(request, "Nie masz uprawnień do wyświetlenia tego quizu.")
    return redirect('home')

@login_required
def my_quizzes_view(request):
    quizzes = Quiz.objects.filter(author=request.user)
    shared_quizzes = request.user.shared_quizzes.all() 
    
    return render(request, 'quizzes/my_quizzes.html', {
        'quizzes': quizzes,
        'shared_quizzes': shared_quizzes
    })

# --- WIDOK GENEROWANIA (ZAKTUALIZOWANY URL I MODEL) ---
@login_required
def quiz_generate_view(request):
    if request.method == 'POST':
        form = QuizGenerationForm(request.POST)
        if form.is_valid():
            topic = form.cleaned_data['topic']
            count = form.cleaned_data['count']
            
            try:
                # Sprawdzenie czy token został załadowany
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

                # Używamy modelu Llama-3-8B-Instruct, który jest szeroko dostępny w darmowym tierze
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
                
                # Czyszczenie markdowna
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
# -------------------------------------------------------

@login_required
def quiz_create_view(request):
    if request.method == 'POST':
        form = QuizForm(request.POST)
        form.fields['shared_with'].queryset = User.objects.exclude(pk=request.user.pk)
        
        if form.is_valid():
            quiz = form.save(commit=False)
            quiz.author = request.user
            quiz.save()
            form.save_m2m()
            messages.success(request, f"Quiz '{quiz.title}' został utworzony.")
            return redirect('quiz-edit', pk=quiz.pk)
    else:
        form = QuizForm()
        form.fields['shared_with'].queryset = User.objects.exclude(pk=request.user.pk)

    return render(request, 'quizzes/quiz_form.html', {'quiz_form': form, 'is_new': True})

@login_required
def quiz_edit_view(request, pk):
    quiz = get_object_or_404(Quiz, pk=pk, author=request.user)
    
    if request.method == 'POST':
        form = QuizForm(request.POST, instance=quiz)
        form.fields['shared_with'].queryset = User.objects.exclude(pk=request.user.pk)
        
        if form.is_valid():
            form.save()
            messages.success(request, "Zapisano zmiany w quizie.")
            return redirect('quiz-edit', pk=quiz.pk)
    else:
        form = QuizForm(instance=quiz)
        form.fields['shared_with'].queryset = User.objects.exclude(pk=request.user.pk)
    
    return render(request, 'quizzes/quiz_form.html', {'quiz_form': form, 'quiz': quiz})

@login_required
def question_create_view(request, quiz_pk):
    quiz = get_object_or_404(Quiz, pk=quiz_pk, author=request.user)
    
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
def question_edit_view(request, pk):
    question = get_object_or_404(Question, pk=pk, quiz__author=request.user)
    
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
def question_delete_view(request, pk):
    question = get_object_or_404(Question, pk=pk, quiz__author=request.user)
    quiz_pk = question.quiz.pk
    if request.method == 'POST':
        question.delete()
        messages.success(request, "Pytanie zostało usunięte.")
        return redirect('quiz-edit', pk=quiz_pk)
    
    return render(request, 'quizzes/question_confirm_delete.html', {'question': question})

@login_required
def quiz_delete_view(request, pk):
    quiz = get_object_or_404(Quiz, pk=pk, author=request.user)
    if request.method == 'POST':
        quiz.delete()
        messages.success(request, "Quiz został usunięty.")
        return redirect('my-quizzes')
    return render(request, 'quizzes/quiz_confirm_delete.html', {'quiz': quiz})

def quiz_take_view(request, pk):
    quiz = get_object_or_404(Quiz, pk=pk)

    if not _can_view_quiz(request.user, quiz):
        messages.error(request, "Nie masz uprawnień do wyświetlenia tego quizu.")
        return redirect('home')

    if quiz.questions.count() == 0:
        messages.info(request, "Ten quiz nie ma jeszcze pytań.")
        return redirect('quiz-detail', pk=quiz.pk)
    
    time_limit_seconds = quiz.time_limit * 60

    if request.method == 'POST':
        total = quiz.questions.count()
        correct_count = 0
        details = []

        for question in quiz.questions.prefetch_related('answers'):
            field = f"q_{question.id}"
            correct_ids = set(question.answers.filter(is_correct=True).values_list('id', flat=True))
            chosen_ids = set()
            
            if question.question_type == Question.QuestionType.SINGLE:
                chosen_id_str = request.POST.get(field)
                if chosen_id_str:
                    try:
                        chosen_ids.add(int(chosen_id_str))
                    except ValueError:
                        pass
            else:
                chosen_id_strs = request.POST.getlist(field)
                for id_str in chosen_id_strs:
                    try:
                        chosen_ids.add(int(id_str))
                    except ValueError:
                        pass 
            
            is_correct = (chosen_ids == correct_ids) and len(chosen_ids) > 0
            if is_correct:
                correct_count += 1
                
            details.append({
                'question': question,
                'answers': list(question.answers.all()),
                'chosen_ids': chosen_ids,
                'correct_ids': correct_ids,
                'is_correct': is_correct,
            })

        score_percent = round((correct_count / total) * 100)
        time_over_bool = request.POST.get('time_over') == '1'

        user_to_save = None
        if request.user.is_authenticated:
            user_to_save = request.user
        
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
    
    questions_data = []
    for q in quiz.questions.prefetch_related('answers'):
        answers = list(q.answers.all())
        random.shuffle(answers)
        questions_data.append({'q': q, 'answers': answers})

    return render(request, 'quizzes/quiz_take.html', {
        'quiz': quiz,
        'questions_data': questions_data,
        'time_limit': time_limit_seconds,
    })

@login_required
def quiz_export_json_view(request, pk):
    quiz = get_object_or_404(Quiz, pk=pk, author=request.user)
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
def quiz_import_json_view(request, pk):
    quiz = get_object_or_404(Quiz, pk=pk, author=request.user)
    
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
            
            for j, ans_data in enumerate(answers_data):
                ans_num = j + 1
                if not isinstance(ans_data, dict):
                     raise ValidationError(f"Pytanie {q_num}, Odpowiedź {ans_num}: Błędny format.")
                
                ans_text = ans_data.get('text')
                is_correct = ans_data.get('is_correct')
                
                if not ans_text:
                    continue
                
                validated_answers.append({'text': ans_text, 'is_correct': is_correct})
            
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