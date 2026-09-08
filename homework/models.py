from django.db import models
from django.contrib.auth.models import User
from courses.models import Course


class Homework(models.Model):
    """Teacher assigns homework to students."""

    title = models.CharField(max_length=200)
    description = models.TextField()
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='homeworks')
    teacher = models.ForeignKey(User, on_delete=models.CASCADE, related_name='homeworks_created')
    due_date = models.DateField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} — {self.course.title}"

    @property
    def submission_count(self):
        return self.submissions.count()

    @property
    def graded_count(self):
        return self.submissions.exclude(grade__isnull=True).exclude(grade='').count()


class HomeworkSubmission(models.Model):
    """Student submits homework."""

    GRADE_CHOICES = [
        ('', 'Not Graded'),
        ('A+', 'A+'),
        ('A', 'A'),
        ('B', 'B'),
        ('C', 'C'),
        ('D', 'D'),
        ('F', 'F'),
    ]

    homework = models.ForeignKey(Homework, on_delete=models.CASCADE, related_name='submissions')
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='homework_submissions')
    submission_text = models.TextField(blank=True)
    file = models.FileField(upload_to='homework_submissions/%Y/%m/', blank=True, null=True)
    grade = models.CharField(max_length=5, choices=GRADE_CHOICES, blank=True)
    feedback = models.TextField(blank=True)
    submitted_at = models.DateTimeField(auto_now_add=True)
    graded_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ('homework', 'student')
        ordering = ['-submitted_at']

    def __str__(self):
        return f"{self.student.get_full_name()} — {self.homework.title}"
