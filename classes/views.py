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

    schedule_items = []
    for day in day_order:
        day_schedules = list(schedules.filter(day=day))
        schedule_items.append((day, day_schedules))

    context = {
        'schedule_items': schedule_items,
        'active_page': 'schedule',
    }
    if user.is_staff or user.is_superuser:
        return render(request, 'classes/schedule_teacher.html', context)
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


# ─── Meetings ────────────────────────────────────────────────────────────

@login_required
def teacher_meetings(request):
    """Teacher creates/manages meetings."""
    from classes.models import Meeting
    from courses.models import Course
    from courses.enrollment_models import Enrollment

    user = request.user
    if not user.is_staff and not user.is_superuser:
        return redirect('classes:student_meetings')

    if user.is_superuser:
        courses = Course.objects.filter(is_active=True)
    else:
        assigned_course_ids = Enrollment.objects.filter(teacher=user, status='approved').values_list('course_id', flat=True).distinct()
        courses = Course.objects.filter(id__in=assigned_course_ids, is_active=True)

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'create':
            title = request.POST.get('title', '').strip()
            description = request.POST.get('description', '').strip()
            course_id = request.POST.get('course_id')
            meeting_type = request.POST.get('meeting_type', 'live')
            meet_link = request.POST.get('meet_link', '').strip()
            scheduled_at = request.POST.get('scheduled_at')
            duration = request.POST.get('duration_minutes', 60)

            if title and course_id and meet_link and scheduled_at:
                course = Course.objects.get(id=course_id)
                meeting = Meeting.objects.create(
                    title=title,
                    description=description,
                    course=course,
                    teacher=user,
                    meeting_type=meeting_type,
                    meet_link=meet_link,
                    scheduled_at=scheduled_at,
                    duration_minutes=int(duration),
                )
                # Auto-add only teacher's assigned students
                if user.is_superuser:
                    enrolled = Enrollment.objects.filter(course=course, status='approved').values_list('student_id', flat=True)
                else:
                    enrolled = Enrollment.objects.filter(course=course, status='approved', teacher=user).values_list('student_id', flat=True)
                meeting.students.set(enrolled)

                # Internal message to students
                from messaging.models import Message
                for sid in enrolled:
                    try:
                        student = User.objects.get(id=sid)
                        Message.objects.create(
                            sender=user,
                            recipient=student,
                            subject=f"🎥 New Meeting: {title} — {course.title}",
                            body=(
                                f"Assalam-o-Alaikum {student.first_name},\n\n"
                                f"A new {meeting.get_meeting_type_display()} has been scheduled.\n\n"
                                f"📌 Title: {title}\n"
                                f"📅 Date: {meeting.scheduled_at.strftime('%B %d, %Y at %I:%M %p')}\n"
                                f"⏱ Duration: {duration} minutes\n\n"
                                f"🔗 Join Link:\n{meet_link}\n\n"
                                f"Click the link above to join the meeting.\n\n"
                                f"JazakAllah Khair!"
                            ),
                        )
                    except User.DoesNotExist:
                        pass

                messages.success(request, f'Meeting "{title}" created and students notified!')
            else:
                messages.error(request, 'All fields are required.')
            return redirect('classes:teacher_meetings')

        elif action == 'delete':
            meeting_id = request.POST.get('meeting_id')
            Meeting.objects.filter(id=meeting_id).delete()
            messages.success(request, 'Meeting deleted.')
            return redirect('classes:teacher_meetings')

    meetings = Meeting.objects.filter(teacher=user).select_related('course').prefetch_related('students')

    context = {
        'courses': courses,
        'meetings': meetings,
    }
    return render(request, 'classes/teacher_meetings.html', context)


@login_required
def student_meetings(request):
    """Student sees upcoming meetings for enrolled courses."""
    from classes.models import Meeting
    from courses.enrollment_models import Enrollment

    user = request.user
    enrolled_courses = Enrollment.objects.filter(student=user, status='approved').values_list('course_id', flat=True)
    meetings = Meeting.objects.filter(course_id__in=enrolled_courses).select_related('course', 'teacher').order_by('-scheduled_at')

    upcoming = meetings.filter(status='upcoming')
    past = meetings.exclude(status='upcoming')

    context = {
        'upcoming_meetings': upcoming,
        'past_meetings': past,
        'active_page': 'meetings',
    }
    return render(request, 'classes/student_meetings.html', context)
