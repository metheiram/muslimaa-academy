from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
from .models import Homework, HomeworkSubmission


def teacher_required(view_func):
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('accounts:login')
        if not request.user.is_staff and not request.user.is_superuser:
            messages.error(request, 'Access denied.')
            return redirect('home')
        return view_func(request, *args, **kwargs)
    return wrapper


@login_required
@teacher_required
def teacher_homework(request):
    """Teacher view — manage homework assignments."""
    from courses.models import Course

    user = request.user
    if user.is_superuser:
        courses = Course.objects.filter(is_active=True)
    else:
        courses = Course.objects.filter(instructor=user, is_active=True)

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'create':
            title = request.POST.get('title', '').strip()
            description = request.POST.get('description', '').strip()
            course_id = request.POST.get('course_id')
            due_date = request.POST.get('due_date')

            if not all([title, description, course_id, due_date]):
                messages.error(request, 'All fields are required.')
            else:
                course = get_object_or_404(Course, id=course_id)
                Homework.objects.create(
                    title=title,
                    description=description,
                    course=course,
                    teacher=user,
                    due_date=due_date,
                )
                messages.success(request, f'Homework "{title}" created for {course.title}!')

                # Notify enrolled students
                from courses.enrollment_models import Enrollment
                enrolled = Enrollment.objects.filter(course=course, status='approved').select_related('student')
                for enr in enrolled:
                    if enr.student.email:
                        try:
                            send_mail(
                                f'New Homework: {title} | Muslimaa Academy',
                                f"Assalam-o-Alaikum {enr.student.first_name},\n\n"
                                f"A new homework has been assigned:\n\n"
                                f"Course: {course.title}\n"
                                f"Title: {title}\n"
                                f"Due Date: {due_date}\n\n"
                                f"{description}\n\n"
                                f"Log in to your dashboard to submit.\n\n"
                                f"Muslimaa Academy Team",
                                settings.DEFAULT_FROM_EMAIL,
                                [enr.student.email],
                                fail_silently=True,
                            )
                        except Exception:
                            pass

            return redirect('homework:teacher_homework')

        elif action == 'delete':
            hw_id = request.POST.get('homework_id')
            Homework.objects.filter(id=hw_id).delete()
            messages.success(request, 'Homework deleted.')
            return redirect('homework:teacher_homework')

    all_homework = Homework.objects.filter(course__in=courses).select_related('course')
    homework_with_subs = []
    for hw in all_homework:
        submissions = hw.submissions.select_related('student').all()
        homework_with_subs.append({'homework': hw, 'submissions': submissions})

    context = {
        'homework_with_subs': homework_with_subs,
        'courses': courses,
        'active_page': 'homework',
    }
    return render(request, 'homework/teacher_homework.html', context)


@login_required
@teacher_required
def grade_submission(request, submission_id):
    """Grade a homework submission."""
    if request.method != 'POST':
        return redirect('homework:teacher_homework')

    submission = get_object_or_404(HomeworkSubmission, id=submission_id)
    grade = request.POST.get('grade', '')
    feedback = request.POST.get('feedback', '').strip()

    submission.grade = grade
    submission.feedback = feedback
    submission.graded_at = timezone.now()
    submission.save()

    # Email student
    if submission.student.email:
        try:
            send_mail(
                f'Homework Graded: {submission.homework.title} | Muslimaa Academy',
                f"Assalam-o-Alaikum {submission.student.first_name},\n\n"
                f"Your homework has been graded:\n\n"
                f"Course: {submission.homework.course.title}\n"
                f"Assignment: {submission.homework.title}\n"
                f"Grade: {grade}\n"
                f"Feedback: {feedback}\n\n"
                f"Log in to view details.\n\n"
                f"Muslimaa Academy Team",
                settings.DEFAULT_FROM_EMAIL,
                [submission.student.email],
                fail_silently=True,
            )
        except Exception:
            pass

    messages.success(request, f'Graded {submission.student.get_full_name()} — {grade}')
    return redirect('homework:teacher_homework')


@login_required
def student_homework(request):
    """Student view — see assignments, submit, view grades."""
    user = request.user
    from courses.enrollment_models import Enrollment

    enrolled_ids = Enrollment.objects.filter(
        student=user, status='approved'
    ).values_list('course_id', flat=True)

    homeworks = Homework.objects.filter(
        course_id__in=enrolled_ids, is_active=True
    ).select_related('course')

    homework_list = []
    for hw in homeworks:
        submission = HomeworkSubmission.objects.filter(
            homework=hw, student=user
        ).first()
        homework_list.append({
            'homework': hw,
            'submission': submission,
            'is_overdue': hw.due_date < timezone.now().date() and not submission,
        })

    context = {
        'homework_list': homework_list,
        'active_page': 'homework',
    }
    return render(request, 'homework/student_homework.html', context)


@login_required
def submit_homework(request, homework_id):
    """Submit homework (student only)."""
    homework = get_object_or_404(Homework, id=homework_id, is_active=True)

    existing = HomeworkSubmission.objects.filter(
        homework=homework, student=request.user
    ).first()

    if existing:
        if existing.grade:
            messages.error(request, 'This homework has already been graded. Cannot resubmit.')
            return redirect('homework:student_homework')

    if request.method == 'POST':
        submission_text = request.POST.get('submission_text', '').strip()
        file = request.FILES.get('file')

        if not submission_text and not file:
            messages.error(request, 'Please provide text or upload a file.')
            return redirect('homework:student_homework')

        if existing:
            existing.submission_text = submission_text
            if file:
                existing.file = file
            existing.save()
        else:
            HomeworkSubmission.objects.create(
                homework=homework,
                student=request.user,
                submission_text=submission_text,
                file=file,
            )

        messages.success(request, f'Homework "{homework.title}" submitted!')
    return redirect('homework:student_homework')
