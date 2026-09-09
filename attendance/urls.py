from django.urls import path
from . import views

app_name = 'attendance'

urlpatterns = [
    path('', views.attendance_view, name='attendance'),
    path('my/', views.student_attendance, name='student_attendance'),
    path('self/', views.self_attendance, name='self_attendance'),
    path('report/', views.attendance_report, name='attendance_report'),
]
