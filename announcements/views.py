from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from django.db import models
from .models import Announcement


def admin_required(view_func):
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('accounts:login')
        if not request.user.is_superuser:
            messages.error(request, 'Access denied. Admin privileges required.')
            return redirect('home')
        return view_func(request, *args, **kwargs)
    return wrapper


@login_required
def announcement_list(request):
    """View all announcements (admin/teacher sees all, students see targeted)."""
    user = request.user

    if user.is_superuser or user.is_staff:
        announcements = Announcement.objects.all()
    else:
        from courses.enrollment_models import Enrollment
        enrolled_course_ids = Enrollment.objects.filter(
            student=user, status='approved'
        ).values_list('course_id', flat=True)

        announcements = Announcement.objects.filter(
            is_active=True
        ).filter(
            models.Q(target='all') | models.Q(course_id__in=enrolled_course_ids)
        )

    context = {
        'announcements': announcements,
        'active_page': 'announcements',
    }

    if user.is_superuser:
        return render(request, 'announcements/admin_announcements.html', context)
    elif user.is_staff:
        return render(request, 'announcements/teacher_announcements.html', context)
    return render(request, 'announcements/student_announcements.html', context)


@login_required
def create_announcement(request):
    """Create a new announcement (admin/teacher only)."""
    from courses.models import Course

    user = request.user
    if not user.is_superuser and not user.is_staff:
        messages.error(request, 'Access denied.')
        return redirect('announcements:announcement_list')

    if user.is_superuser:
        courses = Course.objects.filter(is_active=True)
    else:
        courses = Course.objects.filter(instructor=user, is_active=True)

    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        message_text = request.POST.get('message', '').strip()
        target = request.POST.get('target', 'all')
        priority = request.POST.get('priority', 'normal')
        course_id = request.POST.get('course_id')

        if not title or not message_text:
            messages.error(request, 'Title and message are required.')
            return redirect('announcements:create')

        course = None
        if target == 'course' and course_id:
            course = get_object_or_404(Course, id=course_id)

        announcement = Announcement.objects.create(
            title=title,
            message=message_text,
            target=target,
            course=course,
            priority=priority,
            created_by=user,
        )

        # Send email notifications
        from courses.enrollment_models import Enrollment
        if target == 'all':
            from django.contrib.auth.models import User
            students = User.objects.filter(
                is_superuser=False, is_staff=False, is_active=True
            )
        else:
            enrolled = Enrollment.objects.filter(
                course=course, status='approved'
            ).select_related('student')
            students = [e.student for e in enrolled]

        sent = 0
        for student in students:
            if student.email:
                try:
                    send_mail(
                        f'New Announcement: {announcement.title} | Muslimaa Academy',
                        f"Assalam-o-Alaikum {student.first_name or student.username},\n\n"
                        f"A new announcement has been posted:\n\n"
                        f"Title: {announcement.title}\n"
                        f"Priority: {announcement.get_priority_display()}\n\n"
                        f"{announcement.message}\n\n"
                        f"Log in to your dashboard for details.\n\n"
                        f"Muslimaa Academy Team",
                        settings.DEFAULT_FROM_EMAIL,
                        [student.email],
                        fail_silently=True,
                    )
                    sent += 1
                except Exception:
                    pass

        messages.success(request, f'Announcement "{title}" posted! Email sent to {sent} student(s).')
        return redirect('announcements:announcement_list')

    context = {
        'courses': courses,
        'active_page': 'announcements',
    }
    return render(request, 'announcements/create_announcement.html', context)


@login_required
def delete_announcement(request, announcement_id):
    """Delete an announcement (admin only)."""
    if not request.user.is_superuser:
        messages.error(request, 'Access denied.')
        return redirect('announcements:announcement_list')

    announcement = get_object_or_404(Announcement, id=announcement_id)
    title = announcement.title
    announcement.delete()
    messages.success(request, f'Announcement "{title}" deleted.')
    return redirect('announcements:announcement_list')
