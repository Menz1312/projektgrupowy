# quizzes/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Quiz, Question, Answer
from .forms import QuizForm, QuestionForm, AnswerFormSet
import os, json
from dotenv import load_dotenv
import random
from django.http import HttpResponse
from django.utils.text import slugify
from django.db import transaction
from django.core.exceptions import ValidationError
from django.views.decorators.http import require_POST

load_dotenv()

# Widoki home_view i quiz_detail_view pozostają bez zmian
def home_view(request):
    query = request.GET.get('q', '')
    quizzes = Quiz.objects.filter(visibility='PUBLIC', title__icontains=query)
    return render(request, 'home.html', {'quizzes': quizzes})

def quiz_detail_view(request, pk):
    quiz = get_object_or_404(Quiz, pk=pk)
    is_author = request.user.is_authenticated and quiz.author == request.user
    if quiz.visibility == 'PUBLIC' or is_author:
        return render(request, 'quizzes/quiz_detail.html', {'quiz': quiz})
    messages.error(request, "Nie masz uprawnień do wyświetlenia tego quizu.")
    return redirect('home')

# Widok my_quizzes_view pozostaje bez zmian
@login_required
def my_quizzes_view(request):
    if request.method == 'POST':
        topic = request.POST.get('topic')
        try:
            openai.api_key = os.getenv("OPENAI_API_KEY")
            if not openai.api_key:
                raise ValueError("Klucz API OpenAI nie został skonfigurowany.")
            
            prompt = f"""
            Wygeneruj quiz na temat "{topic}" w języku polskim. Przygotuj 5 pytań.
            Odpowiedz wyłącznie w formacie JSON jako obiekt z kluczem "questions", który zawiera listę obiektów.
            Każdy obiekt: "question" (string), "answers" (lista 4 stringów), "correct_indices" (lista integerów z poprawnymi indeksami od 0).
            """
            client = openai.OpenAI()
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "Jesteś asystentem generującym quizy w formacie JSON."},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"}
            )
            
            quiz_data_str = response.choices[0].message.content
            quiz_data = json.loads(quiz_data_str).get('questions', [])
            
            if not quiz_data:
                 raise ValueError("API nie zwróciło pytań w oczekiwanym formacie.")

            new_quiz = Quiz.objects.create(title=f"Quiz AI: {topic}", author=request.user, visibility='PRIVATE')
            for item in quiz_data:
                q = Question.objects.create(quiz=new_quiz, text=item['question'])
                for i, ans_text in enumerate(item['answers']):
                    Answer.objects.create(question=q, text=ans_text, is_correct=(i in item.get('correct_indices', [])))
            messages.success(request, f"Pomyślnie wygenerowano quiz na temat: {topic}!")

        except Exception as e:
            messages.error(request, f"Wystąpił błąd podczas generowania quizu: {e}")
        return redirect('my-quizzes')
    
    quizzes = Quiz.objects.filter(author=request.user)
    return render(request, 'quizzes/my_quizzes.html', {'quizzes': quizzes})

# Widok quiz_create_view pozostaje bez zmian
@login_required
def quiz_create_view(request):
    if request.method == 'POST':
        form = QuizForm(request.POST)
        if form.is_valid():
            quiz = form.save(commit=False)
            quiz.author = request.user
            quiz.save()
            messages.success(request, f"Quiz '{quiz.title}' został utworzony. Teraz dodaj pytania.")
            return redirect('quiz-edit', pk=quiz.pk)
    else:
        form = QuizForm()
    return render(request, 'quizzes/quiz_form.html', {'quiz_form': form, 'is_new': True})

# Widok quiz_edit_view pozostaje bez zmian
@login_required
def quiz_edit_view(request, pk):
    quiz = get_object_or_404(Quiz, pk=pk, author=request.user)
    if request.method == 'POST':
        form = QuizForm(request.POST, instance=quiz)
        if form.is_valid():
            form.save()
            messages.success(request, "Zapisano zmiany w quizie.")
            return redirect('quiz-edit', pk=quiz.pk)
    else:
        form = QuizForm(instance=quiz)
    
    return render(request, 'quizzes/quiz_form.html', {'quiz_form': form, 'quiz': quiz})

@login_required
def question_create_view(request, quiz_pk):
    quiz = get_object_or_404(Quiz, pk=quiz_pk, author=request.user)
    
    if request.method == 'POST':
        question_form = QuestionForm(request.POST)
        answer_formset = AnswerFormSet(request.POST)
        
        if question_form.is_valid() and answer_formset.is_valid():
            # 🔽 NOWA LOGIKA WALIDACJI
            question_type = question_form.cleaned_data.get('question_type')
            correct_answers_count = 0
            for form in answer_formset.cleaned_data:
                if form.get('is_correct'):
                    correct_answers_count += 1
            
            if question_type == Question.QuestionType.SINGLE and correct_answers_count != 1:
                # Wyświetl błąd, jeśli typ to "Jednokrotny" a liczba odp. nie jest równa 1
                question_form.add_error('question_type', 'Pytanie jednokrotnego wyboru musi mieć dokładnie jedną poprawną odpowiedź.')
            elif question_type == Question.QuestionType.MULTIPLE and correct_answers_count == 0:
                # Wyświetl błąd, jeśli typ to "Wielokrotny" a nie ma żadnej poprawnej odp.
                question_form.add_error('question_type', 'Pytanie wielokrotnego wyboru musi mieć przynajmniej jedną poprawną odpowiedź.')
            else:
                # Walidacja pomyślna, zapisz pytanie i odpowiedzi
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
            # 🔽 NOWA LOGIKA WALIDACJI (taka sama jak w create_view)
            question_type = question_form.cleaned_data.get('question_type')
            correct_answers_count = 0
            for form in answer_formset.cleaned_data:
                # Upewnij się, że formularz nie jest oznaczony do usunięcia (jeśli kiedyś dodasz)
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


# Widok question_delete_view pozostaje bez zmian
@login_required
def question_delete_view(request, pk):
    question = get_object_or_404(Question, pk=pk, quiz__author=request.user)
    quiz_pk = question.quiz.pk
    if request.method == 'POST':
        question.delete()
        messages.success(request, "Pytanie zostało usunięte.")
        return redirect('quiz-edit', pk=quiz_pk)
    
    return render(request, 'quizzes/question_confirm_delete.html', {'question': question})

# Widok quiz_delete_view pozostaje bez zmian
@login_required
def quiz_delete_view(request, pk):
    quiz = get_object_or_404(Quiz, pk=pk, author=request.user)
    if request.method == 'POST':
        quiz.delete()
        messages.success(request, "Quiz został usunięty.")
        return redirect('my-quizzes')
    return render(request, 'quizzes/quiz_confirm_delete.html', {'quiz': quiz})

# Funkcja _can_view_quiz pozostaje bez zmian
def _can_view_quiz(user, quiz):
    return quiz.visibility == 'PUBLIC' or (user.is_authenticated and quiz.author == user)

# 🔽 ZAKTUALIZOWANY WIDOK (Logika oceniania)
def quiz_take_view(request, pk):
    quiz = get_object_or_404(Quiz, pk=pk)

    if not _can_view_quiz(request.user, quiz):
        messages.error(request, "Nie masz uprawnień do wyświetlenia tego quizu.")
        return redirect('home')

    if quiz.questions.count() == 0:
        messages.info(request, "Ten quiz nie ma jeszcze pytań.")
        return redirect('quiz-detail', pk=quiz.pk)
    
    try:
        time_limit = int(request.GET.get('t', '0'))
    except ValueError:
        time_limit = 0
    time_limit = max(0, time_limit)

    if request.method == 'POST':
        total = quiz.questions.count()
        correct_count = 0
        details = []

        # Używamy prefetch_related('answers') dla wydajności
        for question in quiz.questions.prefetch_related('answers'):
            field = f"q_{question.id}"
            correct_ids = set(question.answers.filter(is_correct=True).values_list('id', flat=True))
            
            chosen_ids = set()
            
            if question.question_type == Question.QuestionType.SINGLE:
                # Dla pytań jednokrotnych, używamy .get()
                chosen_id_str = request.POST.get(field)
                if chosen_id_str:
                    try:
                        chosen_ids.add(int(chosen_id_str))
                    except ValueError:
                        pass # Zignoruj niepoprawną wartość
            else:
                # Dla pytań wielokrotnych, używamy .getlist()
                chosen_id_strs = request.POST.getlist(field)
                # Używamy pętli z try-except zamiast map(int, ...) aby być odpornym na błędy
                for id_str in chosen_id_strs:
                    try:
                        chosen_ids.add(int(id_str))
                    except ValueError:
                        pass # Zignoruj niepoprawne wartości
            
            # Logika sprawdzania poprawności pozostaje taka sama
            is_correct = (chosen_ids == correct_ids) and len(chosen_ids) > 0
            if is_correct:
                correct_count += 1
                
            details.append({
                'question': question,
                'answers': list(question.answers.all()), # Odpowiedzi już są w pamięci dzięki prefetch
                'chosen_ids': chosen_ids,
                'correct_ids': correct_ids,
                'is_correct': is_correct,
            })

        score_percent = round((correct_count / total) * 100)
        return render(request, 'quizzes/quiz_result.html', {
            'quiz': quiz,
            'total': total,
            'correct_count': correct_count,
            'score_percent': score_percent,
            'details': details,
            'time_over': request.POST.get('time_over') == '1' # Przekazujemy info o czasie
        })

    # GET -> rozwiązywanie (bez zmian)
    questions_data = []
    for q in quiz.questions.prefetch_related('answers'):
        answers = list(q.answers.all())
        random.shuffle(answers)
        questions_data.append({'q': q, 'answers': answers})

    return render(request, 'quizzes/quiz_take.html', {
        'quiz': quiz,
        'questions_data': questions_data,
        'time_limit': time_limit,
    })

@login_required
def quiz_export_json_view(request, pk):
    """
    Eksportuje wszystkie pytania i odpowiedzi dla danego quizu do pliku JSON.
    """
    quiz = get_object_or_404(Quiz, pk=pk, author=request.user)
    
    questions_data = []
    
    # Używamy prefetch_related dla optymalizacji zapytań
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
        
    json_data = {
        'title': quiz.title,
        'questions': questions_data
    }
    
    # Przygotowanie odpowiedzi HTTP z plikiem JSON
    response = HttpResponse(
        json.dumps(json_data, indent=4, ensure_ascii=False),
        content_type='application/json; charset=utf-8'
    )
    
    # Tworzenie bezpiecznej nazwy pliku
    safe_title = slugify(quiz.title)
    if not safe_title:
        safe_title = 'quiz'
        
    response['Content-Disposition'] = f'attachment; filename="quiz_{quiz.pk}_{safe_title}.json"'
    return response


@login_required
@require_POST # Ten widok powinien przyjmować tylko metodę POST
@transaction.atomic # Używamy transakcji, aby w razie błędu nic się nie zapisało
def quiz_import_json_view(request, pk):
    """
    Importuje pytania z pliku JSON i dodaje je do quizu.
    Wykonuje pełną walidację pliku przed zapisem.
    """
    quiz = get_object_or_404(Quiz, pk=pk, author=request.user)
    
    if 'json_file' not in request.FILES:
        messages.error(request, "Nie wybrano pliku.")
        return redirect('quiz-edit', pk=quiz.pk)

    file = request.FILES['json_file']

    if not file.name.endswith('.json'):
        messages.error(request, "Plik musi być w formacie .json.")
        return redirect('quiz-edit', pk=quiz.pk)

    try:
        # Dekodujemy plik ręcznie, aby mieć pewność kodowania UTF-8
        try:
            file_content = file.read().decode('utf-8')
            data = json.loads(file_content)
        except UnicodeDecodeError:
            raise ValidationError("Plik ma niepoprawne kodowanie. Wymagane jest UTF-8.")
        except json.JSONDecodeError:
            raise ValidationError("Błąd parsowania pliku JSON. Upewnij się, że plik jest poprawny.")

        if 'questions' not in data or not isinstance(data['questions'], list):
            raise ValidationError("Plik JSON musi zawierać klucz 'questions' z listą pytań.")

        questions_to_create = [] # Przechowujemy dane do walidacji

        for i, q_data in enumerate(data['questions']):
            q_num = i + 1
            
            # 1. Walidacja struktury pytania
            if not isinstance(q_data, dict):
                raise ValidationError(f"Pytanie {q_num}: Nie jest poprawnym obiektem JSON.")
                
            text = q_data.get('text')
            if not text or not isinstance(text, str):
                raise ValidationError(f"Pytanie {q_num}: Brak lub niepoprawny klucz 'text'.")

            question_type = q_data.get('question_type', Question.QuestionType.SINGLE)
            if question_type not in Question.QuestionType.values:
                raise ValidationError(f"Pytanie {q_num}: Niepoprawna wartość 'question_type'. Musi być 'SINGLE' lub 'MULTIPLE'.")
            
            explanation = q_data.get('explanation', '')
            answers_data = q_data.get('answers')
            
            # 2. Walidacja struktury odpowiedzi
            if not answers_data or not isinstance(answers_data, list) or len(answers_data) < 2:
                 raise ValidationError(f"Pytanie {q_num} ('{text[:20]}...'): Musi zawierać listę 'answers' z co najmniej 2 odpowiedziami.")

            correct_count = 0
            validated_answers = []
            
            for j, ans_data in enumerate(answers_data):
                ans_num = j + 1
                if not isinstance(ans_data, dict):
                     raise ValidationError(f"Pytanie {q_num}, Odpowiedź {ans_num}: Nie jest poprawnym obiektem JSON.")
                
                ans_text = ans_data.get('text')
                is_correct = ans_data.get('is_correct')
                
                if not ans_text or not isinstance(ans_text, str) or not isinstance(is_correct, bool):
                    raise ValidationError(f"Pytanie {q_num}, Odpowiedź {ans_num}: Niepoprawna struktura (wymagane 'text' (str) i 'is_correct' (bool)).")
                
                if is_correct:
                    correct_count += 1
                validated_answers.append({'text': ans_text, 'is_correct': is_correct})
            
            # 3. Walidacja logiki (zgodnie z question_create_view)
            if question_type == Question.QuestionType.SINGLE and correct_count != 1:
                raise ValidationError(f"Pytanie {q_num} (Jednokrotny): Musi mieć dokładnie 1 poprawną odpowiedź (znaleziono {correct_count}).")
            if question_type == Question.QuestionType.MULTIPLE and correct_count == 0:
                raise ValidationError(f"Pytanie {q_num} (Wielokrotny): Musi mieć przynajmniej 1 poprawną odpowiedź.")
            
            # Jeśli wszystko OK, dodajemy do listy do utworzenia
            questions_to_create.append({
                'q_obj': Question(quiz=quiz, text=text, explanation=explanation, question_type=question_type),
                'answers': validated_answers
            })

        # --- ZAPIS DO BAZY ---
        # Jeśli pętla przeszła bez błędów, zapisujemy wszystko (w ramach transakcji)
        
        num_created = len(questions_to_create)
        
        for q_batch in questions_to_create:
            q = q_batch['q_obj']
            q.save() # Zapisujemy pytanie, aby dostać ID
            
            # Tworzymy odpowiedzi powiązane z tym pytaniem
            answers_to_save = [
                Answer(question=q, text=ans_data['text'], is_correct=ans_data['is_correct'])
                for ans_data in q_batch['answers']
            ]
            Answer.objects.bulk_create(answers_to_save)
        
        messages.success(request, f"Pomyślnie zaimportowano {num_created} pytań.")

    except ValidationError as e:
        # Jawny błąd walidacji
        messages.error(request, f"Błąd walidacji: {e.message}")
        # Transakcja zostanie automatycznie wycofana
    except Exception as e:
        # Inne błędy (np. I/O)
        messages.error(request, f"Wystąpił nieoczekiwany błąd: {e}")
        # Transakcja zostanie automatycznie wycofana

    return redirect('quiz-edit', pk=quiz.pk)