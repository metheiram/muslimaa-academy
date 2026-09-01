from django.shortcuts import render, get_object_or_404
from .models import Course


def course_list(request):
    """Display all courses."""
    courses = Course.objects.filter(is_active=True)
    context = {'courses': courses}
    return render(request, 'courses/course_list.html', context)


def course_detail(request, slug):
    """Display a single course."""
    course = get_object_or_404(Course, slug=slug, is_active=True)
    context = {'course': course}
    return render(request, 'courses/course_detail.html', context)
