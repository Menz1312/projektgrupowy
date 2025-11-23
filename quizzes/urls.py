# quizzes/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('', views.home_view, name='home'),
    path('quiz/<int:pk>/', views.quiz_detail_view, name='quiz-detail'),
    path('my-quizzes/', views.my_quizzes_view, name='my-quizzes'),
    
    # Nowa ścieżka generatora
    path('generate/', views.quiz_generate_view, name='quiz-generate'),
    
    path('create/', views.quiz_create_view, name='quiz-create'),
    path('edit/<int:pk>/', views.quiz_edit_view, name='quiz-edit'),
    path('delete/<int:pk>/', views.quiz_delete_view, name='quiz-delete'),
    
    path('export/<int:pk>/json/', views.quiz_export_json_view, name='quiz-export-json'),
    path('import/<int:pk>/json/', views.quiz_import_json_view, name='quiz-import-json'),

    path('quiz/<int:quiz_pk>/add-question/', views.question_create_view, name='question-create'),
    path('question/<int:pk>/edit/', views.question_edit_view, name='question-edit'),
    path('question/<int:pk>/delete/', views.question_delete_view, name='question-delete'),

    path('quiz/<int:pk>/start/', views.quiz_take_view, name='quiz-start'),
]