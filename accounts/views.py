from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
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
    """Custom login view - admins go to dashboard, others to profile."""
    template_name = 'accounts/login.html'
    
    def get_success_url(self):
        if self.request.user.is_superuser:
            return '/dashboard/'
        return '/accounts/profile/'


@login_required
def profile(request):
    """Display user profile based on role."""
    user = request.user
    if user.is_superuser:
        return redirect('dashboard:admin_dashboard')
    elif user.is_staff:
        template = 'accounts/teacher_profile.html'
        context = {'user': user}
    else:
        from courses.enrollment_models import Enrollment
        from payments.models import Payment
        from django.db.models import Sum
        enrollments = Enrollment.objects.filter(student=user).select_related('course')
        approved_count = enrollments.filter(status='approved').count()
        pending_count = enrollments.filter(status='pending').count()
        payments = Payment.objects.filter(student=user).select_related('course')
        total_paid = payments.filter(status='paid').aggregate(total=Sum('amount'))['total'] or 0
        context = {
            'user': user,
            'enrollments': enrollments,
            'approved_count': approved_count,
            'pending_count': pending_count,
            'payments': payments,
            'total_paid': total_paid,
        }
        template = 'accounts/student_profile.html'
    return render(request, template, context)


def custom_logout(request):
    """Custom logout view that works with GET request."""
    logout(request)
    return redirect('home')
