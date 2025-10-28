from django.shortcuts import render

# Create your views here.
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Quiz
from .forms import QuizForm

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

# ZAKTUALIZOWANY WIDOK
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
    
    # Ten widok teraz tylko edytuje tytuł/widoczność i wyświetla listę pytań
    return render(request, 'quizzes/quiz_form.html', {'quiz_form': form, 'quiz': quiz})

# Widok quiz_delete_view pozostaje bez zmian
@login_required
def quiz_delete_view(request, pk):
    quiz = get_object_or_404(Quiz, pk=pk, author=request.user)
    if request.method == 'POST':
        quiz.delete()
        messages.success(request, "Quiz został usunięty.")
        return redirect('my-quizzes')
    return render(request, 'quizzes/quiz_confirm_delete.html', {'quiz': quiz})