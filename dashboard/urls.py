from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    path('', views.admin_dashboard, name='admin_dashboard'),
    path('students/', views.admin_students, name='admin_students'),
    path('teachers/', views.admin_teachers, name='admin_teachers'),
    path('enrollments/', views.admin_enrollments, name='admin_enrollments'),
    path('fees/', views.admin_fees, name='admin_fees'),
    path('courses/', views.admin_courses, name='admin_courses'),
]
