from django.db import models
from django.contrib.auth.models import User
from courses.models import Course
from courses.enrollment_models import Enrollment


class Payment(models.Model):
    """Payment record for course enrollments."""
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('paid', 'Paid'),
        ('free', 'Free'),
        ('waived', 'Waived'),
    ]
    
    METHOD_CHOICES = [
        ('cash', 'Cash'),
        ('bank', 'Bank Transfer'),
        ('jazzcash', 'JazzCash'),
        ('easypaisa', 'EasyPaisa'),
        ('online', 'Online'),
        ('free', 'Free'),
    ]
    
    enrollment = models.ForeignKey(Enrollment, on_delete=models.CASCADE, related_name='payments')
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='payments')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='payments')
    amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    method = models.CharField(max_length=20, choices=METHOD_CHOICES, default='free')
    notes = models.TextField(blank=True)
    recorded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='recorded_payments')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.student.get_full_name()} - {self.course.title} ({self.status})"
