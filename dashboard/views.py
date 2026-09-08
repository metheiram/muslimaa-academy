from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.db.models import Count, Sum, Q, F
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
from datetime import timedelta
import urllib.parse


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


def build_whatsapp_url(phone, message):
    """Build a WhatsApp wa.me URL with pre-filled message."""
    if not phone:
        return ''
    clean = phone.replace('+', '').replace('-', '').replace(' ', '').replace('(', '').replace(')', '')
    if not clean.startswith('92'):
        clean = '92' + clean.lstrip('0')
    encoded = urllib.parse.quote(message)
    return f"https://wa.me/{clean}?text={encoded}"


def get_payment_info_text():
    """Get formatted payment methods info text."""
    from payments.models import PaymentMethod
    methods = PaymentMethod.objects.filter(is_active=True)
    if not methods.exists():
        return "Contact admin for payment details."
    lines = []
    for pm in methods:
        lines.append(f"*{pm.get_method_display()}*")
        lines.append(f"  Number: {pm.account_number}")
        if pm.account_title:
            lines.append(f"  Title: {pm.account_title}")
        if pm.instructions:
            lines.append(f"  Note: {pm.instructions}")
        lines.append("")
    return "\n".join(lines)


def build_enrollment_approved_message(enrollment):
    """Build WhatsApp receipt message for enrollment approval."""
    payment_info = get_payment_info_text()
    price = enrollment.course.price
    price_text = f"Rs. {int(price)}" if price and price > 0 else "Free"
    return (
        f"Assalam-o-Alaikum {enrollment.student.first_name}! 🌙\n\n"
        f"🎉 *Enrollment Confirmed — Muslimaa Academy*\n\n"
        f"Alhamdulillah! Your enrollment has been approved.\n\n"
        f"📋 *Course:* {enrollment.course.title}\n"
        f"💰 *Fee:* {price_text}\n"
        f"📅 *Enrolled:* {enrollment.enrolled_at.strftime('%d %b, %Y')}\n\n"
        f"💳 *Payment Details:*\n"
        f"{payment_info}\n"
        f"📸 After sending payment, please send the screenshot here on WhatsApp.\n\n"
        f"Once verified, your course access will be activated.\n\n"
        f"JazakAllah Khair! 🤲\n"
        f"Muslimaa Academy Team"
    )


def build_payment_received_message(payment):
    """Build WhatsApp message for payment confirmation."""
    return (
        f"Assalam-o-Alaikum {payment.student.first_name}! 🌙\n\n"
        f"✅ *Payment Received — Muslimaa Academy*\n\n"
        f"📋 *Course:* {payment.course.title}\n"
        f"💰 *Amount:* Rs. {payment.amount}\n"
        f"💳 *Method:* {payment.get_method_display()}\n"
        f"📅 *Date:* {payment.created_at.strftime('%d %b, %Y')}\n\n"
        f"Your payment has been verified. Course access is now active!\n\n"
        f"JazakAllah Khair! 🤲\n"
        f"Muslimaa Academy Team"
    )


def send_email_notification(subject, message, recipient_email):
    """Send email notification silently."""
    try:
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [recipient_email],
            fail_silently=True,
        )
        return True
    except Exception:
        return False


@admin_required
def admin_dashboard(request):
    """Admin dashboard overview."""
    from courses.models import Course
    from courses.enrollment_models import Enrollment
    from workshops.models import Workshop
    from content.models import ContactMessage
    from payments.models import Payment

    today = timezone.now().date()

    if request.method == 'POST' and request.POST.get('action') == 'send_fee_reminders':
        from django.core.management import call_command
        from io import StringIO
        out = StringIO()
        call_command('send_fee_reminders', force_day=today.day, stdout=out)
        output = out.getvalue().strip()
        if 'No unpaid students' in output:
            messages.info(request, 'No unpaid students found for today\'s reminder.')
        else:
            messages.success(request, f'Fee reminders sent! {output}')
        return redirect('dashboard:admin_dashboard')

    total_students = User.objects.filter(is_superuser=False, is_staff=False).count()
    total_courses = Course.objects.filter(is_active=True).count()
    total_workshops = Workshop.objects.filter(is_active=True).count()
    pending_messages = ContactMessage.objects.filter(is_read=False).count()
    pending_enrollments = Enrollment.objects.filter(status='pending').count()
    recent_messages = ContactMessage.objects.all().order_by('-created_at')[:5]

    approved = Enrollment.objects.filter(status='approved')
    paid_enrollment_ids = Payment.objects.filter(status='paid').values_list('enrollment_id', flat=True)
    pending_fees = approved.exclude(id__in=paid_enrollment_ids).count()

    # Chart data — last 6 months
    chart_labels = []
    chart_revenue = []
    chart_enrollments = []
    for i in range(5, -1, -1):
        month_date = today - timedelta(days=30 * i)
        month_label = month_date.strftime('%b %Y')
        chart_labels.append(month_label)
        revenue = Payment.objects.filter(
            status='paid',
            created_at__month=month_date.month,
            created_at__year=month_date.year
        ).aggregate(total=Sum('amount'))['total'] or 0
        chart_revenue.append(float(revenue))
        enroll_count = Enrollment.objects.filter(
            enrolled_at__month=month_date.month,
            enrolled_at__year=month_date.year
        ).count()
        chart_enrollments.append(enroll_count)

    total_revenue = Payment.objects.filter(status='paid').aggregate(total=Sum('amount'))['total'] or 0

    context = {
        'total_students': total_students,
        'total_courses': total_courses,
        'total_workshops': total_workshops,
        'pending_messages': pending_messages,
        'pending_enrollments': pending_enrollments,
        'pending_fees': pending_fees,
        'recent_messages': recent_messages,
        'total_revenue': total_revenue,
        'chart_labels': chart_labels,
        'chart_revenue': chart_revenue,
        'chart_enrollments': chart_enrollments,
    }
    return render(request, 'dashboard/admin.html', context)


@admin_required
def admin_students(request):
    """Manage students - list, add, edit, delete."""
    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'add':
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

        elif action == 'edit':
            user_id = request.POST.get('user_id')
            user = get_object_or_404(User, id=user_id)
            user.first_name = request.POST.get('first_name', user.first_name).strip()
            user.last_name = request.POST.get('last_name', user.last_name).strip()
            user.email = request.POST.get('email', user.email).strip()

            new_password = request.POST.get('password', '').strip()
            if new_password:
                user.set_password(new_password)

            user.save()

            phone = request.POST.get('phone', '').strip()
            user.profile.phone = phone
            user.profile.save()

            messages.success(request, f'Student "{user.get_full_name()}" updated successfully!')
            return redirect('dashboard:admin_students')

        elif action == 'delete':
            user_id = request.POST.get('user_id')
            user = get_object_or_404(User, id=user_id)
            name = user.get_full_name()
            user.delete()
            messages.success(request, f'Student "{name}" deleted successfully!')
            return redirect('dashboard:admin_students')

    students = User.objects.filter(is_superuser=False, is_staff=False).select_related('profile').order_by('-date_joined')
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
    """Manage enrollments - approve/reject with email + WhatsApp."""
    from courses.enrollment_models import Enrollment

    whatsapp_url = ''

    if request.method == 'POST':
        enrollment_id = request.POST.get('enrollment_id')
        action = request.POST.get('action')
        enrollment = get_object_or_404(Enrollment, id=enrollment_id)
        
        if action == 'approve':
            enrollment.status = 'approved'
            enrollment.approved_at = timezone.now()
            enrollment.approved_by = request.user
            enrollment.save()

            # --- Email to student ---
            payment_info = get_payment_info_text()
            price = enrollment.course.price
            price_text = f"Rs. {int(price)}" if price and price > 0 else "Free"
            email_msg = (
                f"Assalam-o-Alaikum {enrollment.student.first_name},\n\n"
                f"Alhamdulillah! Your enrollment in \"{enrollment.course.title}\" has been approved.\n\n"
                f"Course Fee: {price_text}\n\n"
                f"Please complete your payment by sending the fee to:\n\n"
                f"{payment_info}\n"
                f"After sending payment, please send the screenshot on this email ({enrollment.student.email}).\n\n"
                f"Once verified, your course access will be activated.\n\n"
                f"JazakAllah Khair!\n"
                f"Muslimaa Academy Team"
            )
            email_sent = send_email_notification(
                f'Enrollment Approved — {enrollment.course.title} | Muslimaa Academy',
                email_msg,
                enrollment.student.email,
            )

            # --- WhatsApp URL ---
            phone = getattr(enrollment.student.profile, 'phone', '') or ''
            whatsapp_msg = build_enrollment_approved_message(enrollment)
            whatsapp_url = build_whatsapp_url(phone, whatsapp_msg)

            if email_sent:
                messages.success(request, f'Enrollment for {enrollment.student.get_full_name()} approved! Email sent & WhatsApp ready.')
            else:
                messages.success(request, f'Enrollment approved! Email failed but WhatsApp ready.')

            return redirect('dashboard:admin_enrollments')

        elif action == 'reject':
            enrollment.status = 'rejected'
            enrollment.save()
            messages.warning(request, f'Enrollment for {enrollment.student.get_full_name()} rejected.')
            return redirect('dashboard:admin_enrollments')

    pending = Enrollment.objects.filter(status='pending').select_related('student', 'course')
    approved = Enrollment.objects.filter(status='approved').select_related('student', 'course')
    rejected = Enrollment.objects.filter(status='rejected').select_related('student', 'course')

    # Build WhatsApp URLs for all approved enrollments
    approved_with_whatsapp = []
    for enr in approved:
        phone = getattr(enr.student.profile, 'phone', '') or ''
        msg = build_enrollment_approved_message(enr)
        wurl = build_whatsapp_url(phone, msg)
        approved_with_whatsapp.append({'enrollment': enr, 'whatsapp_url': wurl})

    context = {
        'active_tab': 'enrollments',
        'pending_enrollments': pending,
        'approved_enrollments': approved,
        'approved_with_whatsapp': approved_with_whatsapp,
        'rejected_enrollments': rejected,
        'whatsapp_url': whatsapp_url,
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
            name = request.POST.get('name', '').strip() or request.POST.get('pay_method', '').strip()
            method = request.POST.get('pay_method', '').strip()
            account_number = request.POST.get('account_number', '').strip()
            account_title = request.POST.get('account_title', '').strip()
            instructions = request.POST.get('instructions', '').strip()

            if method and account_number:
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

            payment = Payment.objects.create(
                enrollment=enrollment,
                student=enrollment.student,
                course=enrollment.course,
                amount=float(amount),
                status=payment_status,
                method=method,
                notes=notes,
                recorded_by=request.user,
            )

            # --- Email to student ---
            if payment_status == 'paid':
                email_msg = (
                    f"Assalam-o-Alaikum {enrollment.student.first_name},\n\n"
                    f"Your payment has been received!\n\n"
                    f"Course: {enrollment.course.title}\n"
                    f"Amount: Rs. {amount}\n"
                    f"Method: {payment.get_method_display()}\n"
                    f"Date: {payment.created_at.strftime('%d %b, %Y')}\n\n"
                    f"Your course access is now active. JazakAllah Khair!\n\n"
                    f"Muslimaa Academy Team"
                )
                send_email_notification(
                    f'Payment Received — {enrollment.course.title} | Muslimaa Academy',
                    email_msg,
                    enrollment.student.email,
                )

            messages.success(request, f'Payment recorded for {enrollment.student.get_full_name()} — Rs. {amount}.')
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

            # --- Email to student ---
            email_msg = (
                f"Assalam-o-Alaikum {enrollment.student.first_name},\n\n"
                f"Good news! \"{enrollment.course.title}\" has been marked as FREE for you.\n\n"
                f"No payment required. Your course access is now active.\n\n"
                f"JazakAllah Khair!\n"
                f"Muslimaa Academy Team"
            )
            send_email_notification(
                f'Course Free — {enrollment.course.title} | Muslimaa Academy',
                email_msg,
                enrollment.student.email,
            )

            messages.success(request, f'{enrollment.course.title} marked as free for {enrollment.student.get_full_name()}. Email sent.')
            return redirect('dashboard:admin_fees')

    approved = Enrollment.objects.filter(status='approved').select_related('student', 'course')
    payments = Payment.objects.select_related('student', 'course', 'enrollment')
    payment_methods = PaymentMethod.objects.filter(is_active=True)

    total_collected = payments.filter(status='paid').aggregate(total=Sum('amount'))['total'] or 0
    total_pending = approved.count() - payments.count()
    total_free = payments.filter(status='free').count()

    from django.utils import timezone
    from datetime import timedelta
    now = timezone.now()
    this_month = payments.filter(status='paid', created_at__month=now.month, created_at__year=now.year)
    this_month_collected = this_month.aggregate(total=Sum('amount'))['total'] or 0
    this_month_count = this_month.count()

    unpaid_enrollments = []
    for enr in approved:
        has_payment = payments.filter(enrollment=enr).exists()
        if not has_payment:
            days_pending = (now.date() - enr.approved_at.date()).days if enr.approved_at else 0
            unpaid_enrollments.append({'enrollment': enr, 'days_pending': days_pending})

    # Build WhatsApp URLs for each approved enrollment
    approved_with_whatsapp = []
    for enr in approved:
        phone = getattr(enr.student.profile, 'phone', '') or ''
        payment_for_enr = payments.filter(enrollment=enr).first()
        if payment_for_enr and payment_for_enr.status == 'paid':
            msg = build_payment_received_message(payment_for_enr)
        else:
            msg = build_enrollment_approved_message(enr)
        wurl = build_whatsapp_url(phone, msg)
        approved_with_whatsapp.append({'enrollment': enr, 'whatsapp_url': wurl})

    context = {
        'active_tab': 'fees',
        'approved_enrollments': approved,
        'approved_with_whatsapp': approved_with_whatsapp,
        'payments': payments,
        'payment_methods': payment_methods,
        'total_collected': total_collected,
        'total_pending': total_pending,
        'total_free': total_free,
        'this_month_collected': this_month_collected,
        'this_month_count': this_month_count,
        'unpaid_enrollments': unpaid_enrollments,
    }
    return render(request, 'dashboard/fees.html', context)


@admin_required
def admin_courses(request):
    """Manage courses - list, add, edit, delete."""
    from courses.models import Course

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'add':
            title = request.POST.get('title', '').strip()
            description = request.POST.get('description', '').strip()
            short_description = request.POST.get('short_description', '').strip()
            category = request.POST.get('category', 'quranic')
            level = request.POST.get('level', 'beginner')
            duration = request.POST.get('duration', '').strip()
            price = request.POST.get('price', '0')
            features = request.POST.get('features', '').strip()
            curriculum = request.POST.get('curriculum', '').strip()
            faq = request.POST.get('faq', '').strip()
            image_url = request.POST.get('image_url', '').strip()
            meta_title = request.POST.get('meta_title', '').strip()
            meta_description = request.POST.get('meta_description', '').strip()
            instructor_id = request.POST.get('instructor')
            is_active = request.POST.get('is_active') == 'on'
            image = request.FILES.get('image')

            if not title or not description:
                messages.error(request, 'Title and description are required.')
            else:
                course = Course(
                    title=title,
                    description=description,
                    short_description=short_description,
                    category=category,
                    level=level,
                    duration=duration,
                    price=float(price) if price else 0,
                    features=features,
                    curriculum=curriculum,
                    faq=faq,
                    image_url=image_url,
                    meta_title=meta_title,
                    meta_description=meta_description,
                    is_active=is_active,
                )
                if image:
                    course.image = image
                if instructor_id:
                    course.instructor_id = instructor_id
                course.save()
                messages.success(request, f'Course "{title}" created successfully!')
                return redirect('dashboard:admin_courses')

        elif action == 'edit':
            course_id = request.POST.get('course_id')
            course = get_object_or_404(Course, id=course_id)
            course.title = request.POST.get('title', course.title).strip()
            course.description = request.POST.get('description', course.description).strip()
            course.short_description = request.POST.get('short_description', '').strip()
            course.category = request.POST.get('category', course.category)
            course.level = request.POST.get('level', course.level)
            course.duration = request.POST.get('duration', '').strip()
            course.price = float(request.POST.get('price', '0') or '0')
            course.features = request.POST.get('features', '').strip()
            course.curriculum = request.POST.get('curriculum', '').strip()
            course.faq = request.POST.get('faq', '').strip()
            course.image_url = request.POST.get('image_url', '').strip()
            course.meta_title = request.POST.get('meta_title', '').strip()
            course.meta_description = request.POST.get('meta_description', '').strip()
            course.is_active = request.POST.get('is_active') == 'on'

            instructor_id = request.POST.get('instructor')
            if instructor_id:
                course.instructor_id = instructor_id
            else:
                course.instructor = None

            image = request.FILES.get('image')
            if image:
                course.image = image
            course.save()
            messages.success(request, f'Course "{course.title}" updated successfully!')
            return redirect('dashboard:admin_courses')

        elif action == 'delete':
            course_id = request.POST.get('course_id')
            course = get_object_or_404(Course, id=course_id)
            name = course.title
            course.delete()
            messages.success(request, f'Course "{name}" deleted successfully!')
            return redirect('dashboard:admin_courses')

    courses = Course.objects.select_related('instructor').order_by('-created_at')
    teachers = User.objects.filter(is_staff=True, is_superuser=False)
    context = {
        'courses': courses,
        'teachers': teachers,
        'active_tab': 'courses',
    }
    return render(request, 'dashboard/courses.html', context)
