from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.db.models import Count, Sum, Q
from django.utils import timezone
from datetime import timedelta


def admin_required(view_func):
    """Decorator to restrict access to admin users only."""
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('accounts:login')
        if not request.user.is_superuser:
            messages.error(request, 'Access denied. Admin privileges required.')
            return redirect('home')
        return view_func(request, *args, **kwargs)
    return wrapper


@admin_required
def admin_dashboard(request):
    """Admin dashboard overview."""
    from courses.models import Course
    from workshops.models import Workshop
    from content.models import ContactMessage

    today = timezone.now().date()

    total_students = User.objects.filter(is_superuser=False, is_staff=False).count()
    total_courses = Course.objects.filter(is_active=True).count()
    total_workshops = Workshop.objects.filter(is_active=True).count()
    pending_messages = ContactMessage.objects.filter(is_read=False).count()
    recent_messages = ContactMessage.objects.all().order_by('-created_at')[:5]

    context = {
        'total_students': total_students,
        'total_courses': total_courses,
        'total_workshops': total_workshops,
        'pending_messages': pending_messages,
        'recent_messages': recent_messages,
    }
    return render(request, 'dashboard/admin.html', context)


@admin_required
def admin_students(request):
    """Manage students - list and add."""
    if request.method == 'POST':
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        email = request.POST.get('email', '').strip()
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '').strip()

        if not all([first_name, email, username, password]):
            messages.error(request, 'All fields are required.')
        elif User.objects.filter(username=username).exists():
            messages.error(request, 'Username already exists.')
        elif User.objects.filter(email=email).exists():
            messages.error(request, 'Email already exists.')
        else:
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name,
                is_staff=False,
                is_superuser=False,
            )
            messages.success(request, f'Student "{user.get_full_name()}" added successfully!')
            return redirect('dashboard:admin_students')

    students = User.objects.filter(is_superuser=False, is_staff=False).order_by('-date_joined')
    context = {'students': students, 'active_tab': 'students'}
    return render(request, 'dashboard/students.html', context)


@admin_required
def admin_teachers(request):
    """Manage teachers - list and add."""
    if request.method == 'POST':
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        email = request.POST.get('email', '').strip()
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '').strip()
        subject = request.POST.get('subject', '').strip()

        if not all([first_name, email, username, password]):
            messages.error(request, 'All fields are required.')
        elif User.objects.filter(username=username).exists():
            messages.error(request, 'Username already exists.')
        elif User.objects.filter(email=email).exists():
            messages.error(request, 'Email already exists.')
        else:
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name,
                is_staff=True,
                is_superuser=False,
            )
            messages.success(request, f'Teacher "{user.get_full_name()}" added successfully!')
            return redirect('dashboard:admin_teachers')

    teachers = User.objects.filter(is_staff=True, is_superuser=False).order_by('-date_joined')
    context = {'teachers': teachers, 'active_tab': 'teachers'}
    return render(request, 'dashboard/teachers.html', context)


@admin_required
def admin_enrollments(request):
    """Manage enrollments."""
    context = {'active_tab': 'enrollments'}
    return render(request, 'dashboard/enrollments.html', context)


@admin_required
def admin_fees(request):
    """Fee tracking."""
    context = {'active_tab': 'fees'}
    return render(request, 'dashboard/fees.html', context)
