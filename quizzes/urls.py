# quizzes/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('', views.home_view, name='home'),
    path('quiz/<int:pk>/', views.quiz_detail_view, name='quiz-detail'),
    path('my-quizzes/', views.my_quizzes_view, name='my-quizzes'),
    
    # Grupy użytkowników
    path('groups/', views.group_list_view, name='group-list'),
    path('groups/create/', views.group_create_view, name='group-create'),
    path('groups/<int:pk>/edit/', views.group_edit_view, name='group-edit'),
    path('groups/<int:pk>/delete/', views.group_delete_view, name='group-delete'),

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