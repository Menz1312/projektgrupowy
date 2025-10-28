from django.urls import path
from . import views

urlpatterns = [
    path('', views.home_view, name='home'),
    path('quiz/<int:pk>/', views.quiz_detail_view, name='quiz-detail'),
    path('my-quizzes/', views.my_quizzes_view, name='my-quizzes'),
    path('create/', views.quiz_create_view, name='quiz-create'),
    path('edit/<int:pk>/', views.quiz_edit_view, name='quiz-edit'),
    path('delete/<int:pk>/', views.quiz_delete_view, name='quiz-delete'),
    
]