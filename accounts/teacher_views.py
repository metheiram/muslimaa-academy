from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Count, Sum, Q
from django.utils import timezone
from datetime import timedelta
from .models import Profile, TeacherSubscription, SubscriptionPayment


def teacher_register(request):
    """Teacher registration with subscription plan selection."""
    if request.user.is_authenticated and request.user.is_staff:
        return redirect('accounts:teacher_dashboard')
    
    if request.method == 'POST':
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        email = request.POST.get('email', '').strip()
        username = request.POST.get('username', '').strip()
        phone = request.POST.get('phone', '').strip()
        academy_name = request.POST.get('academy_name', '').strip()
        plan = request.POST.get('plan', 'basic')
        password = request.POST.get('password', '')
        password2 = request.POST.get('password2', '')
        
        errors = []
        if not all([first_name, last_name, email, username, phone, password]):
            errors.append('All required fields must be filled.')
        if password != password2:
            errors.append('Passwords do not match.')
        if len(password) < 8:
            errors.append('Password must be at least 8 characters.')
        if User.objects.filter(username=username).exists():
            errors.append('Username already exists.')
        if User.objects.filter(email=email).exists():
            errors.append('Email already registered.')
        
        if errors:
            for error in errors:
                messages.error(request, error)
            return render(request, 'accounts/teacher_register.html', {
                'plans': TeacherSubscription.PLAN_CHOICES,
                'selected_plan': plan,
            })
        
        # Create user
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
        )
        
        # Update profile
        profile = user.profile
        profile.phone = phone
        profile.subject = academy_name
        profile.save()
        
        # Create subscription (pending payment)
        max_students = 10
        monthly_price = 5000
        if plan == 'standard':
            max_students = 20
            monthly_price = 6000
        elif plan == 'premium':
            max_students = 50
            monthly_price = 10000
        
        TeacherSubscription.objects.create(
            teacher=user,
            plan=plan,
            status='pending',
            max_students=max_students,
            monthly_price=monthly_price,
        )
        
        # Auto-login
        login(request, user)
        messages.success(request, f'Welcome {first_name}! Please complete your subscription payment to activate your account.')
        return redirect('accounts:teacher_subscription')
    
    return render(request, 'accounts/teacher_register.html', {
        'plans': TeacherSubscription.PLAN_CHOICES,
        'selected_plan': 'basic',
    })


def teacher_login(request):
    """Teacher login."""
    if request.user.is_authenticated and request.user.is_staff:
        return redirect('accounts:teacher_dashboard')
    
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        
        user = authenticate(request, username=username, password=password)
        if user is not None and user.is_staff:
            login(request, user)
            
            # Check subscription
            try:
                subscription = user.subscription
                subscription.check_expiry()
            except TeacherSubscription.DoesNotExist:
                pass
            
            next_url = request.GET.get('next', 'teacher_dashboard')
            return redirect(next_url)
        else:
            messages.error(request, 'Invalid credentials or not a teacher account.')
    
    return render(request, 'accounts/teacher_login.html')


@login_required
def teacher_logout(request):
    """Teacher logout."""
    logout(request)
    return redirect('accounts:teacher_login')


@login_required
def teacher_dashboard(request):
    """Teacher dashboard - overview of students, subscription, etc."""
    if not request.user.is_staff:
        return redirect('home')
    
    user = request.user
    
    # Get or create subscription
    subscription, created = TeacherSubscription.objects.get_or_create(
        teacher=user,
        defaults={
            'plan': 'basic',
            'status': 'pending',
            'max_students': 10,
            'monthly_price': 5000,
        }
    )
    
    # Check expiry
    subscription.check_expiry()
    
    # Get students
    from courses.enrollment_models import Enrollment
    students = User.objects.filter(
        enrollments__teacher=user,
        enrollments__status='approved'
    ).distinct()
    
    student_count = students.count()
    
    # Update subscription count
    subscription.current_students = student_count
    subscription.save()
    
    # Recent enrollments
    recent_enrollments = Enrollment.objects.filter(
        teacher=user,
        status='approved'
    ).select_related('student', 'course').order_by('-approved_at')[:5]
    
    # Pending enrollments
    pending_count = Enrollment.objects.filter(
        teacher=user,
        status='pending'
    ).count()
    
    # Attendance today
    from attendance.models import Attendance
    today = timezone.now().date()
    today_attendance = Attendance.objects.filter(
        marked_by=user,
        date=today
    ).count()
    
    # Upcoming meetings
    from classes.models import Meeting
    upcoming_meetings = Meeting.objects.filter(
        teacher=user,
        status='upcoming',
        scheduled_at__gte=timezone.now()
    ).order_by('scheduled_at')[:3]
    
    context = {
        'subscription': subscription,
        'students': students[:10],
        'student_count': student_count,
        'recent_enrollments': recent_enrollments,
        'pending_count': pending_count,
        'today_attendance': today_attendance,
        'upcoming_meetings': upcoming_meetings,
        'active_page': 'dashboard',
    }
    return render(request, 'accounts/teacher_dashboard.html', context)


@login_required
def teacher_subscription(request):
    """Teacher subscription management page."""
    if not request.user.is_staff:
        return redirect('home')
    
    subscription, created = TeacherSubscription.objects.get_or_create(
        teacher=request.user,
        defaults={
            'plan': 'basic',
            'status': 'pending',
            'max_students': 10,
            'monthly_price': 5000,
        }
    )
    
    # Payment history
    payments = SubscriptionPayment.objects.filter(
        teacher=request.user
    ).order_by('-created_at')
    
    context = {
        'subscription': subscription,
        'payments': payments,
        'plans': TeacherSubscription.PLAN_CHOICES,
        'active_page': 'subscription',
    }
    return render(request, 'accounts/teacher_subscription.html', context)


@login_required
def teacher_payment_submit(request):
    """Submit subscription payment."""
    if not request.user.is_staff:
        return redirect('home')
    
    if request.method == 'POST':
        subscription = request.user.subscription
        amount = subscription.monthly_price
        method = request.POST.get('method', 'jazzcash')
        transaction_id = request.POST.get('transaction_id', '').strip()
        screenshot = request.FILES.get('screenshot')
        
        payment = SubscriptionPayment.objects.create(
            teacher=request.user,
            subscription=subscription,
            amount=amount,
            method=method,
            transaction_id=transaction_id,
            screenshot=screenshot,
            status='pending',
        )
        
        # Notify all superusers (admin)
        from notifications.models import Notification
        from django.contrib.auth.models import User
        admins = User.objects.filter(is_superuser=True)
        for admin in admins:
            Notification.objects.create(
                user=admin,
                title=f'💳 New Subscription Payment',
                message=f'{request.user.get_full_name()} submitted Rs. {int(amount)} payment via {method}. Plan: {subscription.get_plan_display()}. Please review and approve.',
                notification_type='payment',
            )
        
        messages.success(request, 'Payment submitted! It will be verified shortly.')
        return redirect('accounts:teacher_subscription')
    
    return redirect('accounts:teacher_subscription')


@login_required
def teacher_students(request):
    """Teacher's student management page."""
    if not request.user.is_staff:
        return redirect('home')
    
    subscription = request.user.subscription
    
    # Get students
    from courses.enrollment_models import Enrollment
    students = User.objects.filter(
        enrollments__teacher=request.user,
        enrollments__status='approved'
    ).distinct().select_related('profile')
    
    # Search
    query = request.GET.get('q', '').strip()
    if query:
        students = students.filter(
            Q(first_name__icontains=query) |
            Q(last_name__icontains=query) |
            Q(email__icontains=query)
        )
    
    context = {
        'students': students,
        'student_count': students.count(),
        'subscription': subscription,
        'query': query,
        'active_page': 'students',
    }
    return render(request, 'accounts/teacher_students.html', context)


@login_required
def teacher_add_student(request):
    """Add a new student (teacher only)."""
    if not request.user.is_staff:
        return redirect('home')
    
    subscription = request.user.subscription
    
    if not subscription.can_add_student:
        messages.error(request, f'Student limit reached ({subscription.max_students} students). Please upgrade your plan.')
        return redirect('accounts:teacher_students')
    
    if request.method == 'POST':
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        email = request.POST.get('email', '').strip()
        phone = request.POST.get('phone', '').strip()
        password = request.POST.get('password', '')
        
        errors = []
        if not all([first_name, email, password]):
            errors.append('Name, email, and password are required.')
        if User.objects.filter(email=email).exists():
            errors.append('Email already registered.')
        
        if errors:
            for error in errors:
                messages.error(request, error)
            return render(request, 'accounts/teacher_add_student.html')
        
        # Create student user
        username = email.split('@')[0]
        counter = 1
        while User.objects.filter(username=username).exists():
            username = f"{email.split('@')[0]}{counter}"
            counter += 1
        
        student = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
        )
        
        # Update profile
        student.profile.phone = phone
        student.profile.save()
        
        # Enroll in teacher's course (if any)
        from courses.models import Course
        from courses.enrollment_models import Enrollment
        course = Course.objects.filter(instructor=request.user).first()
        if course:
            Enrollment.objects.create(
                student=student,
                course=course,
                teacher=request.user,
                status='approved',
                approved_at=timezone.now(),
                approved_by=request.user,
            )
        
        # Update subscription count
        subscription.current_students = User.objects.filter(
            enrollments__teacher=request.user,
            enrollments__status='approved'
        ).distinct().count()
        subscription.save()
        
        messages.success(request, f'Student {first_name} {last_name} added successfully!')
        return redirect('accounts:teacher_students')
    
    return render(request, 'accounts/teacher_add_student.html')


@login_required
def teacher_edit_student(request, student_id):
    """Edit student details (teacher only)."""
    if not request.user.is_staff:
        return redirect('home')
    
    student = User.objects.get(id=student_id)
    
    # Verify teacher owns this student
    from courses.enrollment_models import Enrollment
    if not Enrollment.objects.filter(student=student, teacher=request.user, status='approved').exists():
        messages.error(request, 'You do not have permission to edit this student.')
        return redirect('accounts:teacher_students')
    
    if request.method == 'POST':
        student.first_name = request.POST.get('first_name', '').strip()
        student.last_name = request.POST.get('last_name', '').strip()
        student.email = request.POST.get('email', '').strip()
        student.profile.phone = request.POST.get('phone', '').strip()
        student.save()
        student.profile.save()
        
        messages.success(request, f'Student {student.first_name} updated successfully!')
        return redirect('accounts:teacher_students')
    
    return render(request, 'accounts/teacher_edit_student.html', {'student': student})


@login_required
def teacher_remove_student(request, student_id):
    """Remove student (teacher only)."""
    if not request.user.is_staff:
        return redirect('home')
    
    student = User.objects.get(id=student_id)
    
    # Verify teacher owns this student
    from courses.enrollment_models import Enrollment
    enrollment = Enrollment.objects.filter(
        student=student,
        teacher=request.user,
        status='approved'
    ).first()
    
    if enrollment:
        enrollment.status = 'rejected'
        enrollment.save()
        
        # Update subscription count
        subscription = request.user.subscription
        subscription.current_students = User.objects.filter(
            enrollments__teacher=request.user,
            enrollments__status='approved'
        ).distinct().count()
        subscription.save()
        
        messages.success(request, f'Student {student.get_full_name()} removed.')
    
    return redirect('accounts:teacher_students')
