from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta


class Profile(models.Model):
    """User profile for extra info like subject, phone."""
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    phone = models.CharField(max_length=20, blank=True)
    subject = models.CharField(max_length=200, blank=True)
    
    def __str__(self):
        return f"{self.user.get_full_name()} Profile"


class TeacherSubscription(models.Model):
    """Subscription for teachers - SaaS model."""
    
    PLAN_CHOICES = [
        ('basic', 'Basic (1-10 Students)'),
        ('standard', 'Standard (11-20 Students)'),
        ('premium', 'Premium (21-50 Students)'),
    ]
    
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('expired', 'Expired'),
        ('pending', 'Pending Payment'),
        ('cancelled', 'Cancelled'),
    ]
    
    teacher = models.OneToOneField(User, on_delete=models.CASCADE, related_name='subscription')
    plan = models.CharField(max_length=20, choices=PLAN_CHOICES, default='basic')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Limits
    max_students = models.IntegerField(default=10)
    current_students = models.IntegerField(default=0)
    
    # Pricing
    monthly_price = models.DecimalField(max_digits=10, decimal_places=2, default=5000)
    
    # Dates
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Payment info
    last_payment_date = models.DateField(null=True, blank=True)
    last_payment_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    def __str__(self):
        return f"{self.teacher.get_full_name()} - {self.get_plan_display()} ({self.status})"
    
    def save(self, *args, **kwargs):
        # Auto-set limits based on plan
        if self.plan == 'basic':
            self.max_students = 10
            self.monthly_price = 5000
        elif self.plan == 'standard':
            self.max_students = 20
            self.monthly_price = 6000
        elif self.plan == 'premium':
            self.max_students = 5000
            self.monthly_price = 10000
        super().save(*args, **kwargs)
    
    @property
    def is_active(self):
        return self.status == 'active' and self.end_date and self.end_date >= timezone.now().date()
    
    @property
    def can_add_student(self):
        return self.is_active and self.current_students < self.max_students
    
    @property
    def students_remaining(self):
        return max(0, self.max_students - self.current_students)
    
    @property
    def days_until_expiry(self):
        if self.end_date:
            delta = self.end_date - timezone.now().date()
            return max(0, delta.days)
        return 0
    
    def activate(self, months=1):
        """Activate subscription for given months."""
        self.status = 'active'
        self.start_date = timezone.now().date()
        self.end_date = timezone.now().date() + timedelta(days=30 * months)
        self.last_payment_date = timezone.now().date()
        self.last_payment_amount = self.monthly_price
        self.save()
    
    def extend(self, months=1):
        """Extend existing subscription."""
        if self.end_date and self.end_date >= timezone.now().date():
            self.end_date = self.end_date + timedelta(days=30 * months)
        else:
            self.activate(months)
        self.last_payment_date = timezone.now().date()
        self.last_payment_amount = self.monthly_price
        self.save()
    
    def check_expiry(self):
        """Check and update status if expired."""
        if self.end_date and self.end_date < timezone.now().date():
            self.status = 'expired'
            self.save()
            return True
        return False


class SubscriptionPayment(models.Model):
    """Track subscription payments from teachers."""
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]
    
    METHOD_CHOICES = [
        ('jazzcash', 'JazzCash'),
        ('sadapay', 'SadaPay'),
        ('easypaisa', 'EasyPaisa'),
        ('bank', 'Bank Transfer'),
        ('cash', 'Cash'),
    ]
    
    teacher = models.ForeignKey(User, on_delete=models.CASCADE, related_name='subscription_payments')
    subscription = models.ForeignKey(TeacherSubscription, on_delete=models.CASCADE, related_name='payments')
    
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    method = models.CharField(max_length=20, choices=METHOD_CHOICES)
    screenshot = models.ImageField(upload_to='subscription_payments/%Y/%m/', blank=True, null=True)
    transaction_id = models.CharField(max_length=100, blank=True)
    notes = models.TextField(blank=True)
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_subscriptions')
    approved_at = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.teacher.get_full_name()} - Rs. {self.amount} ({self.status})"


def create_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.get_or_create(user=instance)

from django.db.models.signals import post_save
post_save.connect(create_profile, sender=User)
