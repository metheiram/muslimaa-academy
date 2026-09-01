from django.shortcuts import render
from .models import Testimonial


def about(request):
    """Display about page."""
    return render(request, 'content/about.html')


def contact(request):
    """Display contact page."""
    return render(request, 'content/contact.html')


def faq(request):
    """Display FAQ page."""
    return render(request, 'content/faq.html')


def testimonials(request):
    """Display testimonials page."""
    testimonials_list = Testimonial.objects.all()
    context = {'testimonials': testimonials_list}
    return render(request, 'content/testimonials.html', context)
