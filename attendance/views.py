from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.http import JsonResponse
from django.utils import timezone
from datetime import date, timedelta
from .models import Attendance, Schedule


@login_required
def attendance_view(request):
    """Mark and view attendance for teacher's courses."""
    from courses.models import Course

    user = request.user
    if not user.is_staff and not user.is_superuser:
        return redirect('student_dashboard')

    today = date.today()
    courses = Course.objects.filter(instructor=user, is_active=True) if not user.is_superuser else Course.objects.filter(is_active=True)

    selected_course = request.GET.get('course')
    selected_date = request.GET.get('date', str(today))

    students = []
    existing_attendance = {}

    if selected_course:
        from courses.enrollment_models import Enrollment
        course = get_object_or_404(Course, id=selected_course)
        enrolled = Enrollment.objects.filter(course=course, status='approved').select_related('student')
        students = [e.student for e in enrolled]

        attendances = Attendance.objects.filter(
            course=course,
            date=selected_date
        )
        for att in attendances:
            existing_attendance[att.student_id] = att.status

    if request.method == 'POST':
        course_id = request.POST.get('course_id')
        att_date = request.POST.get('date', str(today))
        course = get_object_or_404(Course, id=course_id)

        student_ids = request.POST.getlist('student_ids')
        for sid in student_ids:
            student = get_object_or_404(User, id=sid)
            status = request.POST.get(f'status_{sid}', 'present')
            notes = request.POST.get(f'notes_{sid}', '')

            Attendance.objects.update_or_create(
                student=student,
                course=course,
                date=att_date,
                defaults={
                    'status': status,
                    'marked_by': user,
                    'notes': notes,
                }
            )

        messages.success(request, f'Attendance marked for {course.title} on {att_date}!')
        return redirect(f'/attendance/?course={course_id}&date={att_date}')

    context = {
        'courses': courses,
        'students': students,
        'existing_attendance': existing_attendance,
        'selected_course': selected_course,
        'selected_date': selected_date,
        'active_page': 'attendance',
    }
    return render(request, 'attendance/attendance.html', context)


@login_required
def student_attendance(request):
    """Student views their own attendance."""
    user = request.user
    from courses.enrollment_models import Enrollment

    enrollments = Enrollment.objects.filter(student=user, status='approved').select_related('course')
    courses = [e.course for e in enrollments]

    course_id = request.GET.get('course')
    attendances = Attendance.objects.filter(student=user).select_related('course')

    if course_id:
        attendances = attendances.filter(course_id=course_id)

    total = attendances.count()
    present = attendances.filter(status='present').count()
    absent = attendances.filter(status='absent').count()
    late = attendances.filter(status='late').count()
    excused = attendances.filter(status='excused').count()

    context = {
        'attendances': attendances[:50],
        'courses': courses,
        'selected_course': course_id,
        'total': total,
        'present': present,
        'absent': absent,
        'late': late,
        'excused': excused,
        'active_page': 'attendance',
    }
    return render(request, 'attendance/student_attendance.html', context)
