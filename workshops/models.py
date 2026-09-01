from django.db import models
from django.contrib.auth.models import User


class Workshop(models.Model):
    """Model for workshops offered at Muslimaa Academy."""
    
    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    description = models.TextField()
    date = models.DateField()
    time = models.TimeField()
    duration = models.CharField(max_length=100, default='2 hours')
    instructor = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='workshops_led')
    price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['date', 'time']
        
    def __str__(self):
        return self.title
