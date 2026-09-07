from django.urls import path
from . import views

app_name = 'classes'

urlpatterns = [
    path('', views.schedule_view, name='schedule'),
    path('manage/', views.manage_schedule, name='manage_schedule'),
]
