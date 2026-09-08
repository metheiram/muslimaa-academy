from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
from courses.models import Course
from courses.enrollment_models import Enrollment
import urllib.parse

WHATSAPP_NUMBER = '923184439418'


def get_payment_info_text():
    """Get formatted payment methods info text."""
    from payments.models import PaymentMethod
    methods = PaymentMethod.objects.filter(is_active=True)
    if not methods.exists():
        return "Contact admin for payment details."
    lines = []
    for pm in methods:
        lines.append(f"{pm.get_method_display()}: {pm.account_number}")
        if pm.account_title:
            lines.append(f"  Title: {pm.account_title}")
        if pm.instructions:
            lines.append(f"  Note: {pm.instructions}")
        lines.append("")
    return "\n".join(lines)


def build_student_whatsapp_message(student, course):
    """Build pre-filled WhatsApp message for student to send payment screenshot."""
    price = course.price
    price_text = f"Rs. {int(price)}" if price and price > 0 else "N/A"
    msg = (
        f"Assalam-o-Alaikum!\n\n"
        f"My Name: {student.get_full_name()}\n"
        f"Course: {course.title}\n"
        f"Fee: {price_text}\n\n"
        f"I have sent the payment. Here is my screenshot:"
    )
    encoded = urllib.parse.quote(msg)
    return f"https://wa.me/{WHATSAPP_NUMBER}?text={encoded}"


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

        # --- Build WhatsApp pre-filled link ---
        wa_link = build_student_whatsapp_message(request.user, course)

        # --- Email: enrollment + payment details ---
        price = course.price
        price_text = f"Rs. {int(price)}" if price and price > 0 else "To be confirmed"
        payment_info = get_payment_info_text()

        try:
            send_mail(
                f'Enrollment Received — {course.title} | Muslimaa Academy',
                f"Assalam-o-Alaikum {request.user.first_name},\n\n"
                f"JazakAllah Khair for enrolling in \"{course.title}\"!\n\n"
                f"Course Fee: {price_text}\n\n"
                f"Please send your payment to any of the following accounts:\n\n"
                f"{payment_info}"
                f"After sending payment, send the screenshot on WhatsApp:\n"
                f"📱 WhatsApp: https://wa.me/{WHATSAPP_NUMBER}\n\n"
                f"Or reply to this email with the screenshot attached.\n\n"
                f"Your enrollment is pending approval. Once approved, your course access will be activated.\n\n"
                f"JazakAllah Khair!\n"
                f"Muslimaa Academy Team",
                settings.DEFAULT_FROM_EMAIL,
                [request.user.email],
                fail_silently=True,
            )
        except Exception:
            pass

        messages.success(request, f'Enrollment for {course.title} submitted! Check your email for payment details.')
        return redirect('accounts:student_dashboard')
    
    return render(request, 'courses/enroll.html', {'course': course})


@login_required
def my_enrollments(request):
    """View all enrollments for current user."""
    enrollments = Enrollment.objects.filter(student=request.user).select_related('course')
    enrollments_with_wa = []
    for enr in enrollments:
        wa_url = build_student_whatsapp_message(request.user, enr.course) if enr.status == 'approved' else ''
        enrollments_with_wa.append({'enrollment': enr, 'whatsapp_url': wa_url})
    return render(request, 'courses/my_enrollments.html', {
        'enrollments': enrollments,
        'enrollments_with_wa': enrollments_with_wa,
        'active_page': 'browse',
    })
