from django.db import models
from django.contrib.auth.models import User
from django.utils.text import slugify


class Course(models.Model):
    """Model for courses offered at Muslimaa Academy."""

    LEVEL_CHOICES = [
        ('beginner', 'Beginner'),
        ('intermediate', 'Intermediate'),
        ('advanced', 'Advanced'),
    ]

    CATEGORY_CHOICES = [
        ('quranic', 'Quranic Studies'),
        ('islamic', 'Islamic Studies'),
        ('arabic', 'Arabic Language'),
        ('personal', 'Personal Development'),
        ('kids', 'Kids Programs'),
    ]

    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    description = models.TextField()
    short_description = models.CharField(max_length=300, blank=True, help_text='Brief description for cards')
    category = models.CharField(max_length=100, choices=CATEGORY_CHOICES, default='quranic')
    level = models.CharField(max_length=20, choices=LEVEL_CHOICES, default='beginner')
    duration = models.CharField(max_length=100, default='6 weeks')
    price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    image_url = models.URLField(blank=True, null=True)
    image = models.ImageField(upload_to='courses/', blank=True, null=True)
    instructor = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='courses_taught')
    features = models.TextField(blank=True, help_text='One feature per line')
    curriculum = models.TextField(blank=True, help_text='One module per line')
    faq = models.TextField(blank=True, help_text='Q: question | A: answer — one per line')
    meta_title = models.CharField(max_length=200, blank=True, help_text='SEO title')
    meta_description = models.CharField(max_length=300, blank=True, help_text='SEO description')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
            original_slug = self.slug
            counter = 1
            while Course.objects.filter(slug=self.slug).exclude(pk=self.pk).exists():
                self.slug = f"{original_slug}-{counter}"
                counter += 1
        super().save(*args, **kwargs)

    @property
    def average_rating(self):
        ratings = self.ratings.all()
        if not ratings:
            return 0
        return round(sum(r.rating for r in ratings) / len(ratings), 1)

    @property
    def total_reviews(self):
        return self.ratings.count()


class Rating(models.Model):
    """Student rating and review for a course."""

    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='course_ratings')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='ratings')
    rating = models.IntegerField(default=5)
    review = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('student', 'course')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.student.get_full_name()} - {self.course.title} ({self.rating}/5)"
