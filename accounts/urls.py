from django.urls import path
from django.contrib.auth.views import LogoutView
from . import views
from . import teacher_views
from . import student_portal_views
from .notification_views import student_notifications

app_name = 'accounts'

urlpatterns = [
    path('login/', views.CustomLoginView.as_view(), name='login'),
    path('logout/', views.custom_logout, name='logout'),
    path('register/', views.register, name='register'),
    path('profile/', views.profile, name='profile'),
    path('profile/edit/', views.edit_profile, name='edit_profile'),
    path('password/change/', views.change_password, name='change_password'),
    path('password/forgot/', views.forgot_password, name='forgot_password'),
    path('reset/<str:uidb64>/<str:token>/', views.reset_password, name='reset_password'),
    path('dashboard/', views.student_dashboard, name='student_dashboard'),
    path('notifications/', student_notifications, name='student_notifications'),
    
    # Teacher SaaS URLs
    path('teacher/register/', teacher_views.teacher_register, name='teacher_register'),
    path('teacher/login/', teacher_views.teacher_login, name='teacher_login'),
    path('teacher/logout/', teacher_views.teacher_logout, name='teacher_logout'),
    path('teacher/dashboard/', teacher_views.teacher_dashboard, name='teacher_dashboard'),
    path('teacher/subscription/', teacher_views.teacher_subscription, name='teacher_subscription'),
    path('teacher/payment/', teacher_views.teacher_payment_submit, name='teacher_payment_submit'),
    path('teacher/students/', teacher_views.teacher_students, name='teacher_students'),
    path('teacher/students/add/', teacher_views.teacher_add_student, name='teacher_add_student'),
    path('teacher/students/<int:student_id>/edit/', teacher_views.teacher_edit_student, name='teacher_edit_student'),
    path('teacher/students/<int:student_id>/remove/', teacher_views.teacher_remove_student, name='teacher_remove_student'),
    path('teacher/profile/', teacher_views.teacher_profile, name='teacher_profile'),
    
    # Student Portal (SaaS)
    path('portal/login/', student_portal_views.student_portal_login, name='student_portal_login'),
    path('portal/', student_portal_views.student_portal_dashboard, name='student_portal_dashboard'),
    path('portal/courses/', student_portal_views.student_portal_courses, name='student_portal_courses'),
    path('portal/meetings/', student_portal_views.student_portal_meetings, name='student_portal_meetings'),
    path('portal/homework/', student_portal_views.student_portal_homework, name='student_portal_homework'),
    path('portal/attendance/', student_portal_views.student_portal_attendance, name='student_portal_attendance'),
    path('portal/notifications/', student_portal_views.student_portal_notifications, name='student_portal_notifications'),
    path('portal/logout/', student_portal_views.student_portal_logout, name='student_portal_logout'),
    path('verify-email/<str:token>/', views.verify_email, name='verify_email'),
]
