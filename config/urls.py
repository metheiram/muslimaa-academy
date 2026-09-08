from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView
from courses.views import course_list
from workshops.models import Workshop
from content.models import Testimonial
from courses.models import Course
from accounts.views import student_dashboard, teacher_dashboard


def home_view(request):
    """Home view with context data for courses, workshops, and testimonials."""
    from django.shortcuts import render
    
    courses = Course.objects.filter(is_active=True)[:6]
    workshops = Workshop.objects.filter(is_active=True)[:3]
    testimonials = Testimonial.objects.filter(is_featured=True)[:3]
    
    context = {
        'courses': courses,
        'workshops': workshops,
        'testimonials': testimonials,
    }
    
    return render(request, 'home.html', context)


urlpatterns = [
    path('admin/', admin.site.urls),
    path('', home_view, name='home'),
    path('student/dashboard/', student_dashboard, name='student_dashboard'),
    path('teacher/dashboard/', teacher_dashboard, name='teacher_dashboard'),
    path('courses/', include('courses.urls')),
    path('workshops/', include('workshops.urls')),
    path('accounts/', include('accounts.urls')),
    path('content/', include('content.urls')),
    path('dashboard/', include('dashboard.urls')),
    path('attendance/', include('attendance.urls')),
    path('schedule/', include('classes.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
