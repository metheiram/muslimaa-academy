from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from attendance.models import Schedule
from django.contrib.auth.models import User


@login_required
def schedule_view(request):
    """View class schedule."""
    from courses.models import Course
    from courses.enrollment_models import Enrollment

    user = request.user
    if user.is_staff or user.is_superuser:
        courses = Course.objects.filter(instructor=user, is_active=True) if not user.is_superuser else Course.objects.filter(is_active=True)
    else:
        enrolled = Enrollment.objects.filter(student=user, status='approved').select_related('course')
        courses = [e.course for e in enrolled]

    day_order = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
    schedules = Schedule.objects.filter(course__in=courses, is_active=True).select_related('course', 'teacher').order_by('day', 'start_time')

    schedule_by_day = {}
    for day in day_order:
        schedule_by_day[day] = schedules.filter(day=day)

    context = {
        'schedule_by_day': schedule_by_day,
        'days': day_order,
    }
    return render(request, 'classes/schedule.html', context)


@login_required
def manage_schedule(request):
    """Add/edit/delete schedule entries (admin/teacher only)."""
    from courses.models import Course

    user = request.user
    if not user.is_staff and not user.is_superuser:
        return redirect('classes:schedule')

    if user.is_superuser:
        courses = Course.objects.filter(is_active=True)
        teachers = User.objects.filter(is_staff=True, is_superuser=False)
    else:
        courses = Course.objects.filter(instructor=user, is_active=True)
        teachers = [user]

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'add':
            course_id = request.POST.get('course_id')
            teacher_id = request.POST.get('teacher_id')
            day = request.POST.get('day')
            start_time = request.POST.get('start_time')
            end_time = request.POST.get('end_time')
            room = request.POST.get('room', '')

            course = Course.objects.get(id=course_id)
            teacher = User.objects.get(id=teacher_id)

            Schedule.objects.create(
                course=course,
                teacher=teacher,
                day=day,
                start_time=start_time,
                end_time=end_time,
                room=room,
            )
            messages.success(request, f'Schedule added for {course.title} on {day}!')
            return redirect('classes:manage_schedule')

        elif action == 'delete':
            schedule_id = request.POST.get('schedule_id')
            Schedule.objects.filter(id=schedule_id).delete()
            messages.success(request, 'Schedule entry deleted.')
            return redirect('classes:manage_schedule')

    all_schedules = Schedule.objects.filter(course__in=courses).select_related('course', 'teacher').order_by('day', 'start_time')

    context = {
        'courses': courses,
        'teachers': teachers,
        'all_schedules': all_schedules,
    }
    return render(request, 'classes/manage_schedule.html', context)
