from datetime import timedelta
from django.core.management.base import BaseCommand
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from accounts.models import TeacherSubscription


class Command(BaseCommand):
    help = 'Send trial expiry reminder emails to teachers'

    def handle(self, *args, **options):
        today = timezone.now().date()
        
        expiring_trials = TeacherSubscription.objects.filter(
            is_trial=True,
            status='active',
            trial_ends_at__lte=today + timedelta(days=3),
            trial_ends_at__gte=today,
        )
        
        sent_count = 0
        for sub in expiring_trials:
            days_left = (sub.trial_ends_at - today).days
            
            if days_left <= 0:
                subject = 'Your Free Trial Has Expired - Muslimaa Academy'
                message = (
                    f"Hi {sub.teacher.get_full_name() or sub.teacher.username},\n\n"
                    f"Your free trial for {sub.get_plan_display()} plan has expired.\n\n"
                    f"To continue using Muslimaa Academy without interruption, please subscribe now:\n"
                    f"https://muslimaaacademy.com/accounts/teacher/subscription/\n\n"
                    f"Need help? Reply to this email or WhatsApp us at 03184439418.\n\n"
                    f"Best regards,\nMuslimaa Academy Team"
                )
            elif days_left <= 1:
                subject = 'Final Reminder: Your Trial Ends Tomorrow - Muslimaa Academy'
                message = (
                    f"Hi {sub.teacher.get_full_name() or sub.teacher.username},\n\n"
                    f"Your free trial for {sub.get_plan_display()} plan ends TOMORROW "
                    f"({sub.trial_ends_at.strftime('%b %d, %Y')}).\n\n"
                    f"Subscribe now to keep your students, data, and access:\n"
                    f"https://muslimaaacademy.com/accounts/teacher/subscription/\n\n"
                    f"Best regards,\nMuslimaa Academy Team"
                )
            else:
                subject = f'Your Trial Ends in {days_left} Days - Muslimaa Academy'
                message = (
                    f"Hi {sub.teacher.get_full_name() or sub.teacher.username},\n\n"
                    f"Your free trial for {sub.get_plan_display()} plan ends in {days_left} days "
                    f"({sub.trial_ends_at.strftime('%b %d, %Y')}).\n\n"
                    f"Subscribe now to continue without interruption:\n"
                    f"https://muslimaaacademy.com/accounts/teacher/subscription/\n\n"
                    f"Best regards,\nMuslimaa Academy Team"
                )
            
            try:
                send_mail(
                    subject,
                    message,
                    settings.DEFAULT_FROM_EMAIL,
                    [sub.teacher.email],
                    fail_silently=False,
                )
                sent_count += 1
                self.stdout.write(f'Sent to {sub.teacher.email} ({days_left} days left)')
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'Failed to send to {sub.teacher.email}: {e}'))
        
        self.stdout.write(self.style.SUCCESS(f'Sent {sent_count} trial expiry reminders'))
