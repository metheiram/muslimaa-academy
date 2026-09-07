from django.db import models
from django.contrib.auth.models import User


class Profile(models.Model):
    """User profile for extra info like subject, phone."""
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    phone = models.CharField(max_length=20, blank=True)
    subject = models.CharField(max_length=200, blank=True)
    
    def __str__(self):
        return f"{self.user.get_full_name()} Profile"


def create_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.get_or_create(user=instance)

from django.db.models.signals import post_save
post_save.connect(create_profile, sender=User)
