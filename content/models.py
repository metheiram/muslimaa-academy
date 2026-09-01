from django.db import models


class Testimonial(models.Model):
    """Model for student testimonials."""
    
    author = models.CharField(max_length=200)
    quote = models.TextField()
    course_or_program = models.CharField(max_length=200, blank=True, null=True)
    image_url = models.URLField(blank=True, null=True)
    is_featured = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-is_featured', '-created_at']
        
    def __str__(self):
        return self.author
