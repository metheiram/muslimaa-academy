from django.shortcuts import render, get_object_or_404
from django.db.models import Q
from .models import Course


def course_list(request):
    """Display all courses with search and filter."""
    courses = Course.objects.filter(is_active=True)

    query = request.GET.get('q', '').strip()
    category = request.GET.get('category', '')
    level = request.GET.get('level', '')

    if query:
        courses = courses.filter(
            Q(title__icontains=query) |
            Q(description__icontains=query) |
            Q(short_description__icontains=query)
        )

    if category:
        courses = courses.filter(category=category)

    if level:
        courses = courses.filter(level=level)

    context = {
        'courses': courses,
        'query': query,
        'selected_category': category,
        'selected_level': level,
        'categories': Course.CATEGORY_CHOICES,
        'levels': Course.LEVEL_CHOICES,
    }
    return render(request, 'courses/course_list.html', context)


def course_detail(request, slug):
    """Display a single course."""
    from .models import Rating
    from .enrollment_models import Enrollment
    course = get_object_or_404(Course, slug=slug, is_active=True)
    ratings = Rating.objects.filter(course=course).select_related('student')
    user_rating = None
    user_enrollment = None
    if request.user.is_authenticated:
        user_rating = Rating.objects.filter(student=request.user, course=course).first()
        user_enrollment = Enrollment.objects.filter(student=request.user, course=course).first()
    context = {
        'course': course,
        'ratings': ratings,
        'user_rating': user_rating,
        'user_enrollment': user_enrollment,
    }
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
