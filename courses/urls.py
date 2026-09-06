from django.urls import path
from . import views
from . import enrollment_views

app_name = 'courses'

urlpatterns = [
    path('', views.course_list, name='course_list'),
    path('tajweed/', views.tajweed_detail, name='tajweed'),
    path('hifz/', views.hifz_detail, name='hifz'),
    path('nazra/', views.nazra_detail, name='nazra'),
    path('enrollments/', enrollment_views.my_enrollments, name='my_enrollments'),
    path('<slug:slug>/enroll/', enrollment_views.enroll_course, name='enroll_course'),
    path('<slug:slug>/', views.course_detail, name='course_detail'),
]
