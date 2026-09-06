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


def tajweed_detail(request):
    """Display Tajweed Mastery Course detail page."""
    return render(request, 'courses/tajweed.html')


def hifz_detail(request):
    """Display Hifz & Memorization Program detail page."""
    return render(request, 'courses/hifz.html')


def nazra_detail(request):
    """Display Nazra & Kids Quran Classes detail page."""
    return render(request, 'courses/nazra.html')
