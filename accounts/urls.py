from django.urls import path
from django.contrib.auth.views import LogoutView
from . import views
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
]
