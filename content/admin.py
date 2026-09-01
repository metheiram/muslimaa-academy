from django.contrib import admin
from .models import Testimonial


@admin.register(Testimonial)
class TestimonialAdmin(admin.ModelAdmin):
    list_display = ('author', 'course_or_program', 'is_featured', 'created_at')
    list_filter = ('is_featured', 'created_at')
    search_fields = ('author', 'quote')
