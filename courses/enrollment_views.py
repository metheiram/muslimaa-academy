from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from courses.models import Course
from courses.enrollment_models import Enrollment


@login_required
def enroll_course(request, slug):
    """Student enrolls in a course."""
    course = get_object_or_404(Course, slug=slug)
    
    existing = Enrollment.objects.filter(student=request.user, course=course).first()
    if existing:
        if existing.status == 'approved':
            messages.info(request, f'You are already enrolled in {course.title}.')
        elif existing.status == 'pending':
            messages.info(request, f'Your enrollment for {course.title} is pending approval.')
        else:
            messages.warning(request, f'Your previous enrollment for {course.title} was rejected.')
        return redirect('courses:course_detail', slug=slug)
    
    if request.method == 'POST':
        enrollment = Enrollment.objects.create(
            student=request.user,
            course=course,
            status='pending'
        )
        messages.success(request, f'Enrollment request for {course.title} submitted! Payment details will be sent after approval.')
        return redirect('accounts:profile')
    
    return render(request, 'courses/enroll.html', {'course': course})


@login_required
def my_enrollments(request):
    """View all enrollments for current user."""
    enrollments = Enrollment.objects.filter(student=request.user).select_related('course')
    return render(request, 'courses/my_enrollments.html', {
        'enrollments': enrollments,
        'active_page': 'browse',
    })
