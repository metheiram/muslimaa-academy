from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from django.utils import timezone
from courses.models import Course


def student_portal_login(request):
    """Student login for SaaS portal."""
    if request.user.is_authenticated:
        if request.user.is_superuser:
            return redirect('dashboard:admin_dashboard')
        elif request.user.is_staff:
            return redirect('accounts:teacher_dashboard')
        else:
            return redirect('student_portal_dashboard')
    
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            if user.is_superuser:
                return redirect('dashboard:admin_dashboard')
            elif user.is_staff:
                return redirect('accounts:teacher_dashboard')
            else:
                next_url = request.GET.get('next', 'student_portal_dashboard')
                return redirect(next_url)
        else:
            messages.error(request, 'Invalid username or password.')
    
    return render(request, 'accounts/student_portal_login.html')


@login_required
def student_portal_dashboard(request):
    """Student portal dashboard - shows only their teacher's content."""
    user = request.user
    
    # Get student's teacher
    from courses.models import Enrollment
    enrollments = Enrollment.objects.filter(
        student=user,
        status='approved'
    ).select_related('teacher', 'course')
    
    teachers = User.objects.filter(
        id__in=enrollments.values_list('teacher_id', flat=True)
    ).distinct()
    
    courses = Course.objects.filter(
        id__in=enrollments.values_list('course_id', flat=True)
    )
    
    # Recent notifications
    from notifications.models import Notification
    notifications = Notification.objects.filter(user=user)[:5]
    unread_count = notifications.filter(is_read=False).count()
    
    # Upcoming meetings
    from classes.models import Meeting
    upcoming_meetings = Meeting.objects.filter(
        Q(students=user) | Q(course__in=courses),
        status='upcoming',
        scheduled_at__gte=timezone.now()
    ).order_by('scheduled_at')[:3]
    
    # Pending homework
    from homework.models import Homework
    pending_homework = Homework.objects.filter(
        course__in=courses,
        is_active=True
    ).exclude(
        submissions__student=user
    )[:5]
    
    # Attendance summary
    from attendance.models import Attendance
    total_classes = Attendance.objects.filter(student=user).count()
    present_classes = Attendance.objects.filter(student=user, status='present').count()
    attendance_pct = round((present_classes / total_classes * 100) if total_classes > 0 else 0)
    
    context = {
        'enrollments': enrollments,
        'teachers': teachers,
        'courses': courses,
        'notifications': notifications,
        'unread_count': unread_count,
        'upcoming_meetings': upcoming_meetings,
        'pending_homework': pending_homework,
        'attendance_pct': attendance_pct,
        'total_classes': total_classes,
        'active_page': 'dashboard',
    }
    return render(request, 'accounts/student_portal_dashboard.html', context)


@login_required
def student_portal_courses(request):
    """Student's enrolled courses."""
    user = request.user
    
    from courses.models import Enrollment
    enrollments = Enrollment.objects.filter(
        student=user,
        status='approved'
    ).select_related('course', 'teacher')
    
    context = {
        'enrollments': enrollments,
        'active_page': 'courses',
    }
    return render(request, 'accounts/student_portal_courses.html', context)


@login_required
def student_portal_meetings(request):
    """Student's meetings."""
    user = request.user
    
    from classes.models import Meeting
    from courses.models import Enrollment
    
    enrolled_courses = Enrollment.objects.filter(
        student=user,
        status='approved'
    ).values_list('course_id', flat=True)
    
    upcoming_meetings = Meeting.objects.filter(
        Q(students=user) | Q(course_id__in=enrolled_courses),
        status='upcoming',
        scheduled_at__gte=timezone.now()
    ).order_by('scheduled_at')
    
    past_meetings = Meeting.objects.filter(
        Q(students=user) | Q(course_id__in=enrolled_courses),
        scheduled_at__lt=timezone.now()
    ).order_by('-scheduled_at')[:10]
    
    context = {
        'upcoming_meetings': upcoming_meetings,
        'past_meetings': past_meetings,
        'active_page': 'meetings',
    }
    return render(request, 'accounts/student_portal_meetings.html', context)


@login_required
def student_portal_homework(request):
    """Student's homework."""
    user = request.user
    
    from homework.models import Homework, HomeworkSubmission
    from courses.models import Enrollment
    
    enrolled_courses = Enrollment.objects.filter(
        student=user,
        status='approved'
    ).values_list('course_id', flat=True)
    
    pending_homework = Homework.objects.filter(
        course_id__in=enrolled_courses,
        is_active=True
    ).exclude(
        submissions__student=user
    )
    
    submitted_homework = HomeworkSubmission.objects.filter(
        student=user
    ).select_related('homework', 'homework__course')
    
    context = {
        'pending_homework': pending_homework,
        'submitted_homework': submitted_homework,
        'active_page': 'homework',
    }
    return render(request, 'accounts/student_portal_homework.html', context)


@login_required
def student_portal_attendance(request):
    """Student's attendance."""
    user = request.user
    
    from attendance.models import Attendance
    from courses.models import Enrollment
    
    enrolled_courses = Enrollment.objects.filter(
        student=user,
        status='approved'
    ).values_list('course_id', flat=True)
    
    attendance = Attendance.objects.filter(
        student=user
    ).select_related('course').order_by('-date')
    
    # Stats
    total = attendance.count()
    present = attendance.filter(status='present').count()
    absent = attendance.filter(status='absent').count()
    late = attendance.filter(status='late').count()
    pct = round((present / total * 100) if total > 0 else 0)
    
    context = {
        'attendance': attendance,
        'total': total,
        'present': present,
        'absent': absent,
        'late': late,
        'attendance_pct': pct,
        'active_page': 'attendance',
    }
    return render(request, 'accounts/student_portal_attendance.html', context)


@login_required
def student_portal_notifications(request):
    """Student's notifications."""
    from notifications.models import Notification
    
    notifications = Notification.objects.filter(user=request.user)
    
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'mark_all_read':
            notifications.update(is_read=True)
            messages.success(request, 'All notifications marked as read.')
        elif action == 'mark_read':
            notif_id = request.POST.get('notification_id')
            Notification.objects.filter(id=notif_id, user=request.user).update(is_read=True)
        elif action == 'delete':
            notif_id = request.POST.get('notification_id')
            Notification.objects.filter(id=notif_id, user=request.user).delete()
    
    context = {
        'notifications': notifications,
        'active_page': 'notifications',
    }
    return render(request, 'accounts/student_portal_notifications.html', context)


@login_required
def student_portal_logout(request):
    """Student logout."""
    logout(request)
    return redirect('student_portal_login')
