from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.contrib import messages
from django import forms
from django.contrib.auth.forms import PasswordChangeForm


class RegisterForm(forms.ModelForm):
    """Form for user registration."""
    
    password = forms.CharField(widget=forms.PasswordInput)
    password2 = forms.CharField(widget=forms.PasswordInput, label='Confirm Password')
    
    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'email', 'username')
        
    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        password2 = cleaned_data.get("password2")
        
        if password and password2 and password != password2:
            raise forms.ValidationError("Passwords do not match")
        return cleaned_data


def register(request):
    """Handle user registration with phone/WhatsApp."""
    if request.method == 'POST':
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        email = request.POST.get('email', '').strip()
        username = request.POST.get('username', '').strip()
        phone = request.POST.get('phone', '').strip()
        password = request.POST.get('password', '')
        password2 = request.POST.get('password2', '')

        errors = []
        if not all([first_name, email, username, password]):
            errors.append('All required fields must be filled.')
        if password != password2:
            errors.append('Passwords do not match.')
        if User.objects.filter(username=username).exists():
            errors.append('Username already exists.')
        if User.objects.filter(email=email).exists():
            errors.append('Email already registered.')
        
        # Password validation
        from django.contrib.auth.password_validation import validate_password
        from django.core.exceptions import ValidationError as DjangoValidationError
        try:
            validate_password(password)
        except DjangoValidationError as e:
            for error in e.messages:
                errors.append(error)

        if errors:
            for e in errors:
                messages.error(request, e)
            return render(request, 'accounts/register.html', {
                'form_data': request.POST
            })

        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
        )
        if phone:
            user.profile.phone = phone
            user.profile.save()

        # Auto-login after registration
        from django.contrib.auth import login
        login(request, user)

        messages.success(request, f'Welcome {user.first_name}! 🎉 Browse our courses and enroll to start your learning journey.')
        return redirect('student_dashboard')

    context = {'form_data': {}}
    return render(request, 'accounts/register.html', context)


class CustomLoginView(LoginView):
    """Custom login view - admins go to dashboard, teachers to teacher dashboard, students to student dashboard."""
    template_name = 'accounts/login.html'
    
    def get_success_url(self):
        next_url = self.request.GET.get('next') or self.request.POST.get('next')
        if next_url and next_url.startswith('/') and '//' not in next_url:
            return next_url
        if self.request.user.is_superuser:
            return '/dashboard/'
        elif self.request.user.is_staff:
            return '/teacher/dashboard/'
        return '/student/dashboard/'


@login_required
def student_dashboard(request):
    """Student dashboard with courses, payments, schedule."""
    from courses.enrollment_models import Enrollment
    from payments.models import Payment
    from courses.models import Course
    from django.db.models import Sum
    from django.utils import timezone

    user = request.user
    enrollments = Enrollment.objects.filter(student=user).select_related('course', 'course__instructor')
    payments = Payment.objects.filter(student=user).select_related('course')

    approved_enrollments = enrollments.filter(status='approved')
    pending_enrollments = enrollments.filter(status='pending')
    total_paid = payments.filter(status='paid').aggregate(total=Sum('amount'))['total'] or 0
    total_pending_payment = payments.filter(status='pending').aggregate(total=Sum('amount'))['total'] or 0

    # Upcoming meetings — only meetings where student is assigned
    from classes.models import Meeting
    upcoming_meetings = Meeting.objects.filter(
        students=user,
        status='upcoming',
        scheduled_at__gte=timezone.now()
    ).select_related('course', 'teacher').order_by('scheduled_at')[:3]

    # Pending homework
    from homework.models import HomeworkSubmission
    pending_homework = HomeworkSubmission.objects.filter(
        student=user,
        homework__due_date__gte=timezone.now(),
        submitted_at__isnull=True
    ).select_related('homework', 'homework__course')[:3]

    # Attendance stats
    from attendance.models import Attendance
    total_attendance = Attendance.objects.filter(student=user).count()
    present_count = Attendance.objects.filter(student=user, status='present').count()
    absent_count = Attendance.objects.filter(student=user, status='absent').count()
    attendance_pct = round((present_count / total_attendance * 100), 1) if total_attendance > 0 else 0

    # Notifications
    from notifications.models import Notification
    notifications = Notification.objects.filter(user=user)[:10]
    unread_count = Notification.objects.filter(user=user, is_read=False).count()

    context = {
        'enrollments': enrollments,
        'approved_enrollments': approved_enrollments,
        'pending_enrollments': pending_enrollments,
        'payments': payments,
        'total_paid': total_paid,
        'total_pending_payment': total_pending_payment,
        'approved_count': approved_enrollments.count(),
        'pending_count': pending_enrollments.count(),
        'upcoming_meetings': upcoming_meetings,
        'pending_homework': pending_homework,
        'total_attendance': total_attendance,
        'present_count': present_count,
        'absent_count': absent_count,
        'attendance_pct': attendance_pct,
        'active_page': 'dashboard',
        'notifications': notifications,
        'unread_count': unread_count,
    }
    return render(request, 'accounts/student_dashboard.html', context)


@login_required
def teacher_dashboard(request):
    """Teacher dashboard with assigned students, courses, schedule."""
    from courses.enrollment_models import Enrollment
    from courses.models import Course
    from payments.models import Payment
    from django.utils import timezone

    user = request.user
    enrolled_students = Enrollment.objects.filter(
        teacher=user,
        status='approved'
    ).select_related('student', 'course')

    total_students = enrolled_students.values('student').distinct().count()
    assigned_course_ids = enrolled_students.values_list('course_id', flat=True).distinct()
    total_courses = assigned_course_ids.count()
    total_pending = Enrollment.objects.filter(
        teacher=user,
        status='pending'
    ).count()

    # Upcoming meetings
    from classes.models import Meeting
    upcoming_meetings = Meeting.objects.filter(
        teacher=user,
        status='upcoming',
        scheduled_at__gte=timezone.now()
    ).select_related('course').order_by('scheduled_at')[:5]

    # Pending homework submissions
    from homework.models import Homework, HomeworkSubmission
    pending_submissions = HomeworkSubmission.objects.filter(
        homework__teacher=user,
        grade__isnull=True
    ).select_related('student', 'homework')[:5]
    total_pending_submissions = HomeworkSubmission.objects.filter(
        homework__teacher=user,
        grade__isnull=True
    ).count()

    # Recent attendance
    from attendance.models import Attendance
    from django.utils import timezone as tz
    recent_attendance = Attendance.objects.filter(
        marked_by=user
    ).select_related('student', 'course').order_by('-date')[:5]

    context = {
        'courses_taught': Course.objects.filter(id__in=assigned_course_ids, is_active=True),
        'enrolled_students': enrolled_students,
        'total_students': total_students,
        'total_courses': total_courses,
        'total_pending': total_pending,
        'upcoming_meetings': upcoming_meetings,
        'pending_submissions': pending_submissions,
        'total_pending_submissions': total_pending_submissions,
        'recent_attendance': recent_attendance,
        'active_page': 'dashboard',
    }
    return render(request, 'accounts/teacher_dashboard.html', context)


@login_required
def profile(request):
    """Display user profile based on role."""
    user = request.user
    if user.is_superuser:
        return redirect('dashboard:admin_dashboard')
    elif user.is_staff:
        return redirect('teacher_dashboard')
    else:
        return redirect('student_dashboard')


@login_required
def edit_profile(request):
    """Edit user profile - name, email, phone, subject."""
    user = request.user

    if request.method == 'POST':
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        email = request.POST.get('email', '').strip()
        phone = request.POST.get('phone', '').strip()
        subject = request.POST.get('subject', '').strip()

        if not first_name or not email:
            messages.error(request, 'First name and email are required.')
        elif User.objects.filter(email=email).exclude(id=user.id).exists():
            messages.error(request, 'This email is already in use.')
        else:
            user.first_name = first_name
            user.last_name = last_name
            user.email = email
            user.save()

            user.profile.phone = phone
            if user.is_staff:
                user.profile.subject = subject
            user.profile.save()

            messages.success(request, 'Profile updated successfully!')
            return redirect('accounts:edit_profile')

    context = {'profile_user': user, 'active_page': 'profile'}
    if user.is_staff and not user.is_superuser:
        return render(request, 'accounts/edit_profile_teacher.html', context)
    return render(request, 'accounts/edit_profile.html', context)


@login_required
def change_password(request):
    """Change password for any logged-in user."""
    if request.method == 'POST':
        form = PasswordChangeForm(user=request.user, data=request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            messages.success(request, 'Password changed successfully!')
            return redirect('accounts:edit_profile')
        else:
            for error in form.errors.values():
                messages.error(request, error.as_text())
    else:
        form = PasswordChangeForm(user=request.user)

    template = 'accounts/change_password.html'
    if request.user.is_staff and not request.user.is_superuser:
        template = 'accounts/change_password_teacher.html'

    context = {'form': form, 'active_page': 'profile'}
    return render(request, template, context)


def forgot_password(request):
    """Password reset via email."""
    if request.method == 'POST':
        email = request.POST.get('email', '').strip()
        # Always show same message to prevent user enumeration
        if User.objects.filter(email=email).exists():
            from django.contrib.auth.tokens import default_token_generator
            from django.utils.http import urlsafe_base64_encode
            from django.utils.encoding import force_bytes
            from django.core.mail import send_mail
            from django.conf import settings

            user = User.objects.get(email=email)
            token = default_token_generator.make_token(user)
            uid = urlsafe_base64_encode(force_bytes(user.pk))

            reset_url = f"{request.scheme}://{request.get_host()}/accounts/reset/{uid}/{token}/"

            try:
                send_mail(
                    'Password Reset - Muslimaa Academy',
                    f'Salam {user.first_name},\n\n'
                    f'You requested a password reset. Click the link below to reset your password:\n\n'
                    f'{reset_url}\n\n'
                    f'If you did not request this, please ignore this email.\n\n'
                    f'JazakAllah Khair!\n'
                    f'Muslimaa Academy Team',
                    settings.DEFAULT_FROM_EMAIL,
                    [email],
                    fail_silently=True,
                )
            except Exception:
                pass
        
        # Always show same message regardless of email existence
        messages.success(request, 'If an account exists with this email, a password reset link has been sent.')
        return redirect('accounts:login')

    return render(request, 'accounts/forgot_password.html')


def reset_password(request, uidb64, token):
    """Reset password with token."""
    from django.utils.http import urlsafe_base64_decode
    from django.utils.encoding import force_str
    from django.contrib.auth.tokens import default_token_generator

    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    if user is not None and default_token_generator.check_token(user, token):
        if request.method == 'POST':
            password = request.POST.get('password', '')
            password2 = request.POST.get('password2', '')

            if not password:
                messages.error(request, 'Password is required.')
            elif password != password2:
                messages.error(request, 'Passwords do not match.')
            else:
                # Password validation
                from django.contrib.auth.password_validation import validate_password
                from django.core.exceptions import ValidationError as DjangoValidationError
                try:
                    validate_password(password, user)
                except DjangoValidationError as e:
                    for error in e.messages:
                        messages.error(request, error)
                    return render(request, 'accounts/reset_password.html', {'valid': True})
                
                user.set_password(password)
                user.save()
                messages.success(request, 'Password reset successful! You can now login.')
                return redirect('accounts:login')

        return render(request, 'accounts/reset_password.html', {'valid': True})
    else:
        messages.error(request, 'Invalid or expired reset link.')
        return redirect('accounts:login')


def custom_logout(request):
    """Custom logout view that works with GET request."""
    logout(request)
    return redirect('home')
