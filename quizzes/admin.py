# quizzes/admin.py
from django.contrib import admin
from .models import Quiz, Question, Answer, QuizAttempt, QuizGroup, QuizUserPermission, QuizGroupPermission

class AnswerInline(admin.TabularInline):
    model = Answer
    extra = 2

class QuestionInline(admin.TabularInline):
    model = Question
    extra = 1
    show_change_link = True

class QuizUserPermissionInline(admin.TabularInline):
    model = QuizUserPermission
    extra = 1
    autocomplete_fields = ['user']

class QuizGroupPermissionInline(admin.TabularInline):
    model = QuizGroupPermission
    extra = 1

@admin.register(Quiz)
class QuizAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'visibility', 'time_limit')
    list_filter = ('visibility', 'author')
    search_fields = ('title', 'author__username')
    inlines = [QuizUserPermissionInline, QuizGroupPermissionInline, QuestionInline]

@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ('text', 'quiz', 'question_type')
    inlines = [AnswerInline]

@admin.register(QuizGroup)
class QuizGroupAdmin(admin.ModelAdmin):
    filter_horizontal = ('members',)

admin.site.register(QuizAttempt)