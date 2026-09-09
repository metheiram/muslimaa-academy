from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
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
    if user.is_superuser:
        courses = Course.objects.filter(is_active=True)
    else:
        from courses.enrollment_models import Enrollment
        assigned_course_ids = Enrollment.objects.filter(teacher=user, status='approved').values_list('course_id', flat=True).distinct()
        courses = Course.objects.filter(id__in=assigned_course_ids, is_active=True)

    selected_course = request.GET.get('course')
    selected_date = request.GET.get('date', str(today))

    students = []
    existing_attendance = {}

    if selected_course:
        from courses.enrollment_models import Enrollment
        course = get_object_or_404(Course, id=selected_course)
        if user.is_superuser:
            enrolled = Enrollment.objects.filter(course=course, status='approved').select_related('student')
        else:
            enrolled = Enrollment.objects.filter(course=course, status='approved', teacher=user).select_related('student')
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

    students_with_status = []
    for s in students:
        students_with_status.append({
            'student': s,
            'existing_status': existing_attendance.get(s.id, 'present'),
        })

    context = {
        'courses': courses,
        'students_with_status': students_with_status,
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
    percentage = round((present / total * 100), 1) if total > 0 else 0

    context = {
        'attendances': attendances[:50],
        'courses': courses,
        'selected_course': course_id,
        'total': total,
        'present': present,
        'absent': absent,
        'late': late,
        'excused': excused,
        'percentage': percentage,
        'active_page': 'attendance',
    }
    return render(request, 'attendance/student_attendance.html', context)


@login_required
def attendance_report(request):
    """Generate printable attendance report for student."""
    user = request.user
    from courses.enrollment_models import Enrollment
    from datetime import date
    import calendar

    month = int(request.GET.get('month', date.today().month))
    year = int(request.GET.get('year', date.today().year))
    course_id = request.GET.get('course')

    month = max(1, min(12, month))
    month_name = calendar.month_name[month]
    days_in_month = calendar.monthrange(year, month)[1]

    from django.utils import timezone
    start_date = date(year, month, 1)
    end_date = date(year, month, days_in_month)

    enrollments = Enrollment.objects.filter(student=user, status='approved').select_related('course')
    courses = [e.course for e in enrollments]

    course_filter = None
    if course_id:
        course_filter = int(course_id)
        attendances = Attendance.objects.filter(
            student=user, date__gte=start_date, date__lte=end_date, course_id=course_id
        ).select_related('course')
    else:
        attendances = Attendance.objects.filter(
            student=user, date__gte=start_date, date__lte=end_date
        ).select_related('course')

    total = attendances.count()
    present = attendances.filter(status='present').count()
    absent = attendances.filter(status='absent').count()
    late = attendances.filter(status='late').count()
    excused = attendances.filter(status='excused').count()
    percentage = round((present / total * 100), 1) if total > 0 else 0

    course_attendance = {}
    for att in attendances:
        cname = att.course.title
        if cname not in course_attendance:
            course_attendance[cname] = {'total': 0, 'present': 0, 'absent': 0, 'late': 0, 'excused': 0}
        course_attendance[cname]['total'] += 1
        course_attendance[cname][att.status] += 1

    context = {
        'student': user,
        'month': month,
        'year': year,
        'month_name': month_name,
        'courses': courses,
        'selected_course': course_id,
        'attendances': attendances,
        'total': total,
        'present': present,
        'absent': absent,
        'late': late,
        'excused': excused,
        'percentage': percentage,
        'course_attendance': course_attendance,
        'active_page': 'attendance',
    }
    return render(request, 'attendance/attendance_report.html', context)


@login_required
def self_attendance(request):
    """Student marks their own attendance for enrolled courses."""
    from courses.enrollment_models import Enrollment
    from datetime import date

    user = request.user
    today = date.today()

    approved_enrollments = Enrollment.objects.filter(
        student=user, status='approved'
    ).select_related('course', 'teacher')

    # Check which courses already have attendance marked today
    courses_with_attendance = []
    courses_pending = []
    for enr in approved_enrollments:
        att = Attendance.objects.filter(
            student=user, course=enr.course, date=today
        ).first()
        courses_with_attendance.append({
            'enrollment': enr,
            'attendance': att,
        })
        if not att:
            courses_pending.append(enr)

    if request.method == 'POST':
        course_id = request.POST.get('course_id')
        status = request.POST.get('status', 'present')

        if course_id:
            course = get_object_or_404(Course, id=course_id)
            existing = Attendance.objects.filter(
                student=user, course=course, date=today
            ).first()
            if existing:
                messages.warning(request, f'Attendance for {course.title} already marked today as {existing.get_status_display()}.')
            else:
                Attendance.objects.create(
                    student=user,
                    course=course,
                    date=today,
                    status=status,
                    marked_by=user,
                    notes='Self-marked',
                )
                messages.success(request, f'Attendance marked for {course.title} — {status.title()}!')

        return redirect('attendance:self_attendance')

    context = {
        'courses_with_attendance': courses_with_attendance,
        'courses_pending': courses_pending,
        'today': today,
        'active_page': 'attendance',
    }
    return render(request, 'attendance/self_attendance.html', context)
