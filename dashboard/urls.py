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
    
    # SaaS Teacher Management
    path('teachers-saas/', views.admin_teachers_saas, name='admin_teachers_saas'),
    path('teachers-saas/<int:teacher_id>/', views.admin_teacher_detail, name='admin_teacher_detail'),
    path('teachers-saas/<int:teacher_id>/change-plan/', views.admin_change_plan, name='admin_change_plan'),
    path('subscription/<int:payment_id>/approve/', views.admin_approve_subscription, name='admin_approve_subscription'),
    path('subscription/<int:payment_id>/reject/', views.admin_reject_subscription, name='admin_reject_subscription'),
]
