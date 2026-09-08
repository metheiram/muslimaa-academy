from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
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

        # --- Email: enrollment pending confirmation ---
        price = course.price
        price_text = f"Rs. {int(price)}" if price and price > 0 else "To be confirmed"
        try:
            send_mail(
                f'Enrollment Received — {course.title} | Muslimaa Academy',
                f"Assalam-o-Alaikum {request.user.first_name},\n\n"
                f"JazakAllah Khair for enrolling in \"{course.title}\"!\n\n"
                f"Course Fee: {price_text}\n\n"
                f"We have received your enrollment request. Our team will review it shortly.\n\n"
                f"You will receive an email with payment details once your enrollment is approved.\n\n"
                f"If you have any questions, feel free to reply to this email.\n\n"
                f"Muslimaa Academy Team",
                settings.DEFAULT_FROM_EMAIL,
                [request.user.email],
                fail_silently=True,
            )
        except Exception:
            pass

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
