from django.db import models
from django.contrib.auth.models import User
from courses.models import Course


class Meeting(models.Model):
    """Live class meeting — teacher creates with Google Meet/Zoom link."""
    
    TYPE_CHOICES = [
        ('live', 'Live Class'),
        ('doubt', 'Doubt Session'),
        ('exam', 'Exam'),
        ('recording', 'Recording Shared'),
    ]
    
    STATUS_CHOICES = [
        ('upcoming', 'Upcoming'),
        ('ongoing', 'Ongoing'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]
    
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='meetings')
    teacher = models.ForeignKey(User, on_delete=models.CASCADE, related_name='meetings_taught')
    meeting_type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='live')
    meet_link = models.URLField(help_text='Google Meet / Zoom link')
    scheduled_at = models.DateTimeField()
    duration_minutes = models.IntegerField(default=60, help_text='Duration in minutes')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='upcoming')
    created_at = models.DateTimeField(auto_now_add=True)
    
    # Students who are enrolled (auto-populated or manual)
    students = models.ManyToManyField(User, blank=True, related_name='meetings', help_text='Students invited to this meeting')
    
    class Meta:
        ordering = ['-scheduled_at']
    
    def __str__(self):
        return f"{self.title} — {self.course.title} ({self.get_status_display()})"
    
    @property
    def is_upcoming(self):
        from django.utils import timezone
        return self.scheduled_at > timezone.now() and self.status == 'upcoming'
    
    @property
    def time_until(self):
        from django.utils import timezone
        now = timezone.now()
        diff = self.scheduled_at - now
        if diff.total_seconds() < 0:
            return "Started"
        hours = int(diff.total_seconds() // 3600)
        minutes = int((diff.total_seconds() % 3600) // 60)
        if hours > 24:
            days = hours // 24
            return f"in {days} day{'s' if days > 1 else ''}"
        elif hours > 0:
            return f"in {hours}h {minutes}m"
        else:
            return f"in {minutes}m"
