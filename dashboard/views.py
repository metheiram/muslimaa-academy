from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.db.models import Count, Sum, Q, F
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
    from courses.enrollment_models import Enrollment
    from workshops.models import Workshop
    from content.models import ContactMessage

    today = timezone.now().date()

    total_students = User.objects.filter(is_superuser=False, is_staff=False).count()
    total_courses = Course.objects.filter(is_active=True).count()
    total_workshops = Workshop.objects.filter(is_active=True).count()
    pending_messages = ContactMessage.objects.filter(is_read=False).count()
    pending_enrollments = Enrollment.objects.filter(status='pending').count()
    recent_messages = ContactMessage.objects.all().order_by('-created_at')[:5]

    context = {
        'total_students': total_students,
        'total_courses': total_courses,
        'total_workshops': total_workshops,
        'pending_messages': pending_messages,
        'pending_enrollments': pending_enrollments,
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
    """Manage teachers - list, add, edit, delete."""
    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'add':
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
                if subject:
                    user.profile.subject = subject
                    user.profile.save()
                messages.success(request, f'Teacher "{user.get_full_name()}" added successfully!')
                return redirect('dashboard:admin_teachers')

        elif action == 'edit':
            user_id = request.POST.get('user_id')
            user = get_object_or_404(User, id=user_id)
            user.first_name = request.POST.get('first_name', user.first_name).strip()
            user.last_name = request.POST.get('last_name', user.last_name).strip()
            user.email = request.POST.get('email', user.email).strip()
            subject = request.POST.get('subject', '').strip()
            
            new_password = request.POST.get('password', '').strip()
            if new_password:
                user.set_password(new_password)
            
            user.save()
            user.profile.subject = subject
            user.profile.save()
            messages.success(request, f'Teacher "{user.get_full_name()}" updated successfully!')
            return redirect('dashboard:admin_teachers')

        elif action == 'delete':
            user_id = request.POST.get('user_id')
            user = get_object_or_404(User, id=user_id)
            name = user.get_full_name()
            user.delete()
            messages.success(request, f'Teacher "{name}" deleted successfully!')
            return redirect('dashboard:admin_teachers')

    teachers = User.objects.filter(is_staff=True, is_superuser=False).select_related('profile').order_by('-date_joined')
    context = {'teachers': teachers, 'active_tab': 'teachers'}
    return render(request, 'dashboard/teachers.html', context)


@admin_required
def admin_enrollments(request):
    """Manage enrollments - approve/reject."""
    from courses.enrollment_models import Enrollment
    from django.utils import timezone

    if request.method == 'POST':
        enrollment_id = request.POST.get('enrollment_id')
        action = request.POST.get('action')
        enrollment = get_object_or_404(Enrollment, id=enrollment_id)
        
        if action == 'approve':
            enrollment.status = 'approved'
            enrollment.approved_at = timezone.now()
            enrollment.approved_by = request.user
            enrollment.save()
            messages.success(request, f'Enrollment for {enrollment.student.get_full_name()} in {enrollment.course.title} approved!')
        elif action == 'reject':
            enrollment.status = 'rejected'
            enrollment.save()
            messages.warning(request, f'Enrollment for {enrollment.student.get_full_name()} in {enrollment.course.title} rejected.')
        return redirect('dashboard:admin_enrollments')

    pending = Enrollment.objects.filter(status='pending').select_related('student', 'course')
    approved = Enrollment.objects.filter(status='approved').select_related('student', 'course')
    rejected = Enrollment.objects.filter(status='rejected').select_related('student', 'course')
    
    context = {
        'active_tab': 'enrollments',
        'pending_enrollments': pending,
        'approved_enrollments': approved,
        'rejected_enrollments': rejected,
    }
    return render(request, 'dashboard/enrollments.html', context)


@admin_required
def admin_fees(request):
    """Fee tracking - manage payments and payment methods."""
    from payments.models import Payment, PaymentMethod
    from courses.enrollment_models import Enrollment
    from django.db.models import Sum

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'add_payment_method':
            name = request.POST.get('name', '').strip()
            method = request.POST.get('pay_method', '').strip()
            account_number = request.POST.get('account_number', '').strip()
            account_title = request.POST.get('account_title', '').strip()
            instructions = request.POST.get('instructions', '').strip()

            if name and method and account_number:
                PaymentMethod.objects.create(
                    name=name,
                    method=method,
                    account_number=account_number,
                    account_title=account_title,
                    instructions=instructions,
                )
                messages.success(request, f'Payment method "{name}" added successfully!')
            else:
                messages.error(request, 'Name, method, and account number are required.')
            return redirect('dashboard:admin_fees')

        elif action == 'delete_payment_method':
            method_id = request.POST.get('method_id')
            PaymentMethod.objects.filter(id=method_id).delete()
            messages.success(request, 'Payment method deleted.')
            return redirect('dashboard:admin_fees')

        elif action == 'add_payment':
            enrollment_id = request.POST.get('enrollment_id')
            enrollment = get_object_or_404(Enrollment, id=enrollment_id)
            amount = request.POST.get('amount', '0')
            method = request.POST.get('method', 'free')
            notes = request.POST.get('notes', '')
            payment_status = request.POST.get('payment_status', 'paid')

            Payment.objects.create(
                enrollment=enrollment,
                student=enrollment.student,
                course=enrollment.course,
                amount=float(amount),
                status=payment_status,
                method=method,
                notes=notes,
                recorded_by=request.user,
            )
            messages.success(request, f'Payment recorded for {enrollment.student.get_full_name()} — Rs. {amount}')
            return redirect('dashboard:admin_fees')

        elif action == 'mark_free':
            enrollment_id = request.POST.get('enrollment_id')
            enrollment = get_object_or_404(Enrollment, id=enrollment_id)
            Payment.objects.create(
                enrollment=enrollment,
                student=enrollment.student,
                course=enrollment.course,
                amount=0,
                status='free',
                method='free',
                notes='Course marked as free',
                recorded_by=request.user,
            )
            messages.success(request, f'{enrollment.course.title} marked as free for {enrollment.student.get_full_name()}.')
            return redirect('dashboard:admin_fees')

    approved = Enrollment.objects.filter(status='approved').select_related('student', 'course')
    payments = Payment.objects.select_related('student', 'course', 'enrollment')
    payment_methods = PaymentMethod.objects.filter(is_active=True)

    total_collected = payments.filter(status='paid').aggregate(total=Sum('amount'))['total'] or 0
    total_pending = approved.count() - payments.count()
    total_free = payments.filter(status='free').count()

    context = {
        'active_tab': 'fees',
        'approved_enrollments': approved,
        'payments': payments,
        'payment_methods': payment_methods,
        'total_collected': total_collected,
        'total_pending': total_pending,
        'total_free': total_free,
    }
    return render(request, 'dashboard/fees.html', context)
