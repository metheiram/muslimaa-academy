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
    """Handle user registration."""
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data['password'])
            user.save()
            return redirect('accounts:login')
    else:
        form = RegisterForm()
    
    context = {'form': form}
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
    else:
        template = 'accounts/student_profile.html'
    context = {'user': user}
    return render(request, template, context)


def custom_logout(request):
    """Custom logout view that works with GET request."""
    logout(request)
    return redirect('home')
