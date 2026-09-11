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
        lines.append(f"*{pm.get_method_display()}*")
        lines.append(f"  Number: {pm.account_number}")
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


class Command(BaseCommand):
    help = 'Send monthly fee reminders to students on their enrollment anniversary date'

    def handle(self, *args, **options):
        from courses.enrollment_models import Enrollment
        from payments.models import Payment

        today = date.today()
        payment_info = get_payment_info_text()

        approved = Enrollment.objects.filter(status='approved').select_related('student', 'course')
        payments = Payment.objects.filter(status='paid')

        anniversary_students = []
        for enr in approved:
            has_payment = payments.filter(enrollment=enr).exists()
            if (enr.enrolled_at
                    and enr.enrolled_at.day == today.day
                    and enr.enrolled_at.month != today.month
                    and enr.course.price and enr.course.price > 0
                    and not has_payment):
                anniversary_students.append(enr)

        if not anniversary_students:
            self.stdout.write(self.style.SUCCESS(f'No students have their enrollment anniversary on {today.strftime("%B %d")}.'))
            return

        sent_count = 0
        for enr in anniversary_students:
            student = enr.student
            course = enr.course
            amount = course.price
            first_name = student.first_name or student.username
            enrolled_date = enr.enrolled_at.strftime('%d %b, %Y')
            months_ago = (today.year - enr.enrolled_at.year) * 12 + today.month - enr.enrolled_at.month

            whatsapp_link = build_whatsapp_link(student.get_full_name(), course.title, amount)

            email_msg = (
                f"Assalam-o-Alaikum {first_name},\n\n"
                f"This is your monthly fee reminder. Today marks {months_ago} month{'s' if months_ago > 1 else ''} since you enrolled.\n\n"
                f"Course: {course.title}\n"
                f"Fee: Rs. {int(amount)}\n"
                f"Enrolled on: {enrolled_date}\n\n"
                f"Please send your payment to any of the following accounts:\n\n"
                f"{payment_info}\n"
                f"After sending payment, send the screenshot on WhatsApp:\n"
                f"📱 WhatsApp: {whatsapp_link}\n\n"
                f"Or upload it directly from your dashboard.\n\n"
                f"JazakAllah Khair!\n"
                f"Muslimaa Academy Team"
            )

            try:
                send_mail(
                    f'Monthly Fee Reminder — {course.title} | Muslimaa Academy',
                    email_msg,
                    settings.DEFAULT_FROM_EMAIL,
                    [student.email],
                    fail_silently=True,
                )
                sent_count += 1
                self.stdout.write(f'  Sent to {student.get_full_name()} ({student.email}) — {course.title} — {months_ago} month(s) ago')
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'  Failed to send to {student.email}: {e}'))

        self.stdout.write(self.style.SUCCESS(
            f'\nDone! {sent_count} reminder(s) sent on {today.strftime("%B %d")}.'
        ))
