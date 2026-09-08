from django.db import models
from django.contrib.auth.models import User
from courses.models import Course


class Announcement(models.Model):
    """Announcements from admin/teacher to students."""

    TARGET_CHOICES = [
        ('all', 'All Students'),
        ('course', 'Specific Course'),
    ]

    PRIORITY_CHOICES = [
        ('normal', 'Normal'),
        ('important', 'Important'),
        ('urgent', 'Urgent'),
    ]

    title = models.CharField(max_length=200)
    message = models.TextField()
    target = models.CharField(max_length=10, choices=TARGET_CHOICES, default='all')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, null=True, blank=True, related_name='announcements')
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='normal')
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='announcements')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title

    @property
    def target_display(self):
        if self.target == 'all':
            return 'All Students'
        return f'Course: {self.course.title}' if self.course else 'All Students'
