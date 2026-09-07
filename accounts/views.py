from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.contrib import messages
from django import forms


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

        messages.success(request, 'Registration successful! You will receive enrollment details via email and WhatsApp within 24 hours after admin approval.')
        return redirect('accounts:login')

    context = {'form_data': {}}
    return render(request, 'accounts/register.html', context)


class CustomLoginView(LoginView):
    """Custom login view - admins go to dashboard, teachers to teacher dashboard, students to student dashboard."""
    template_name = 'accounts/login.html'
    
    def get_success_url(self):
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

    user = request.user
    enrollments = Enrollment.objects.filter(student=user).select_related('course', 'course__instructor')
    payments = Payment.objects.filter(student=user).select_related('course')

    approved_enrollments = enrollments.filter(status='approved')
    pending_enrollments = enrollments.filter(status='pending')
    total_paid = payments.filter(status='paid').aggregate(total=Sum('amount'))['total'] or 0
    total_pending_payment = payments.filter(status='pending').aggregate(total=Sum('amount'))['total'] or 0

    context = {
        'enrollments': enrollments,
        'approved_enrollments': approved_enrollments,
        'pending_enrollments': pending_enrollments,
        'payments': payments,
        'total_paid': total_paid,
        'total_pending_payment': total_pending_payment,
        'approved_count': approved_enrollments.count(),
        'pending_count': pending_enrollments.count(),
    }
    return render(request, 'accounts/student_dashboard.html', context)


@login_required
def teacher_dashboard(request):
    """Teacher dashboard with assigned students, courses, schedule."""
    from courses.enrollment_models import Enrollment
    from courses.models import Course
    from payments.models import Payment

    user = request.user
    courses_taught = Course.objects.filter(instructor=user, is_active=True)
    enrolled_students = Enrollment.objects.filter(
        course__in=courses_taught,
        status='approved'
    ).select_related('student', 'course')

    total_students = enrolled_students.values('student').distinct().count()
    total_courses = courses_taught.count()
    total_pending = Enrollment.objects.filter(
        course__in=courses_taught,
        status='pending'
    ).count()

    context = {
        'courses_taught': courses_taught,
        'enrolled_students': enrolled_students,
        'total_students': total_students,
        'total_courses': total_courses,
        'total_pending': total_pending,
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


def custom_logout(request):
    """Custom logout view that works with GET request."""
    logout(request)
    return redirect('home')
