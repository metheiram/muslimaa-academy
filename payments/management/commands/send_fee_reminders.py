from django.core.management.base import BaseCommand
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from datetime import date
import urllib.parse

WHATSAPP_NUMBER = '923184439418'


def get_payment_info_text():
    from payments.models import PaymentMethod
    methods = PaymentMethod.objects.filter(is_active=True)
    if not methods.exists():
        return "Contact admin for payment details."
    lines = []
    for pm in methods:
        lines.append(f"{pm.get_method_display()}: {pm.account_number}")
        if pm.account_title:
            lines.append(f"  Title: {pm.account_title}")
        if pm.instructions:
            lines.append(f"  Note: {pm.instructions}")
        lines.append("")
    return "\n".join(lines)


def build_whatsapp_link(student_name, course_name, amount):
    msg = (
        f"Assalam-o-Alaikum!\n\n"
        f"I am {student_name}.\n"
        f"Course: {course_name}\n"
        f"Fee: Rs. {int(amount)}\n\n"
        f"I have sent the payment. Here is my screenshot:"
    )
    encoded = urllib.parse.quote(msg)
    return f"https://wa.me/{WHATSAPP_NUMBER}?text={encoded}"


REMINDER_TEMPLATES = {
    1: {
        'subject': 'Fee Reminder — Payment Due | Muslimaa Academy',
        'greeting': 'Assalam-o-Alaikum',
        'message': (
            '{greeting} {first_name},\n\n'
            'This is a friendly reminder that your course fee is due.\n\n'
            'Course: {course}\n'
            'Fee: Rs. {amount}\n\n'
            'Please send your payment to any of the following accounts:\n\n'
            '{payment_info}\n'
            'After sending payment, send the screenshot on WhatsApp:\n'
            '📱 WhatsApp: {whatsapp_link}\n\n'
            'Or upload it directly from your dashboard.\n\n'
            'JazakAllah Khair!\n'
            'Muslimaa Academy Team'
        ),
        'tag': 'first',
    },
    3: {
        'subject': 'Fee Reminder (2nd) — Payment Due Soon | Muslimaa Academy',
        'greeting': 'Assalam-o-Alaikum',
        'message': (
            '{greeting} {first_name},\n\n'
            'This is your second reminder. Your course fee is still pending.\n\n'
            'Course: {course}\n'
            'Fee: Rs. {amount}\n\n'
            'Please send your payment to any of the following accounts:\n\n'
            '{payment_info}\n'
            'After sending payment, send the screenshot on WhatsApp:\n'
            '📱 WhatsApp: {whatsapp_link}\n\n'
            'Or upload it directly from your dashboard.\n\n'
            'Please complete the payment soon to avoid any disruption.\n\n'
            'JazakAllah Khair!\n'
            'Muslimaa Academy Team'
        ),
        'tag': 'second',
    },
    5: {
        'subject': 'URGENT: Fee Payment Last Date Today | Muslimaa Academy',
        'greeting': 'Assalam-o-Alaikum',
        'message': (
            '{greeting} {first_name},\n\n'
            '⚠️ This is your FINAL reminder. Today is the last date to pay your course fee.\n\n'
            'Course: {course}\n'
            'Fee: Rs. {amount}\n\n'
            'Please send your payment IMMEDIATELY to any of the following accounts:\n\n'
            '{payment_info}\n'
            'After sending payment, send the screenshot on WhatsApp:\n'
            '📱 WhatsApp: {whatsapp_link}\n\n'
            'Or upload it directly from your dashboard.\n\n'
            'If payment is not received today, your course access may be affected.\n\n'
            'JazakAllah Khair!\n'
            'Muslimaa Academy Team'
        ),
        'tag': 'final',
    },
}


class Command(BaseCommand):
    help = 'Send fee reminders to students with pending payments on 1st, 3rd, and 5th of each month'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force-day',
            type=int,
            choices=[1, 3, 5],
            help='Force send reminder for a specific day (1, 3, or 5) regardless of today\'s date',
        )

    def handle(self, *args, **options):
        from courses.enrollment_models import Enrollment
        from payments.models import Payment
        from django.db.models import Sum

        today = date.today()
        day = options.get('force_day') or today.day

        if day not in [1, 3, 5]:
            self.stdout.write(self.style.WARNING(f'Today is day {day}. Reminders only sent on 1st, 3rd, and 5th.'))
            return

        template = REMINDER_TEMPLATES[day]
        payment_info = get_payment_info_text()

        approved = Enrollment.objects.filter(status='approved').select_related('student', 'course')
        payments = Payment.objects.filter(status='paid')

        unpaid_students = []
        for enr in approved:
            has_payment = payments.filter(enrollment=enr).exists()
            if not has_payment and enr.course.price and enr.course.price > 0:
                unpaid_students.append(enr)

        if not unpaid_students:
            self.stdout.write(self.style.SUCCESS(f'No unpaid students found for day {day} reminder.'))
            return

        sent_count = 0
        for enr in unpaid_students:
            student = enr.student
            course = enr.course
            amount = course.price
            first_name = student.first_name or student.username

            whatsapp_link = build_whatsapp_link(student.get_full_name(), course.title, amount)

            email_msg = template['message'].format(
                greeting=template['greeting'],
                first_name=first_name,
                course=course.title,
                amount=int(amount),
                payment_info=payment_info,
                whatsapp_link=whatsapp_link,
            )

            try:
                send_mail(
                    template['subject'],
                    email_msg,
                    settings.DEFAULT_FROM_EMAIL,
                    [student.email],
                    fail_silently=True,
                )
                sent_count += 1
                self.stdout.write(f'  Sent to {student.get_full_name()} ({student.email}) — {course.title}')
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'  Failed to send to {student.email}: {e}'))

        self.stdout.write(self.style.SUCCESS(
            f'\nDone! {sent_count} reminder(s) sent (day {day} — {template["tag"]}).'
        ))
