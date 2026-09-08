from django.urls import path
from . import views

app_name = 'homework'

urlpatterns = [
    path('teacher/', views.teacher_homework, name='teacher_homework'),
    path('student/', views.student_homework, name='student_homework'),
    path('submit/<int:homework_id>/', views.submit_homework, name='submit_homework'),
    path('grade/<int:submission_id>/', views.grade_submission, name='grade_submission'),
]
