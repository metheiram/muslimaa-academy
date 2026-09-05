from django.shortcuts import render, redirect
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings
from .models import Testimonial, ContactMessage


def about(request):
    """Display about page."""
    return render(request, 'content/about.html')


def contact(request):
    """Handle contact form submission."""
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        email = request.POST.get('email', '').strip()
        subject_choice = request.POST.get('subject', 'other')
        message_text = request.POST.get('message', '').strip()
        
        if not name or not email or not message_text:
            messages.error(request, 'Please fill in all required fields.')
            return render(request, 'content/contact.html')
        
        # Save to database
        contact_msg = ContactMessage.objects.create(
            name=name,
            email=email,
            subject=subject_choice,
            message=message_text,
        )
        
        # Send email to site owner
        subject_display = dict(ContactMessage.SUBJECT_CHOICES).get(subject_choice, 'Other')
        
        email_subject = f'New Contact Form: {subject_display} - from {name}'
        email_body = f"""
You have received a new message from your website contact form.

Name: {name}
Email: {email}
Subject: {subject_display}

Message:
{message_text}

---
This message was sent from the Muslimaa Academy contact form.
        """
        
        try:
            send_mail(
                subject=email_subject,
                message=email_body,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[settings.CONTACT_EMAIL],
                fail_silently=False,
            )
            messages.success(request, 'Your message has been sent successfully! We will get back to you within 24 hours.')
        except Exception as e:
            messages.success(request, 'Your message has been received! We will get back to you soon.')
        
        return redirect('content:contact')
    
    return render(request, 'content/contact.html')


def faq(request):
    """Display FAQ page."""
    return render(request, 'content/faq.html')


def testimonials(request):
    """Display testimonials page."""
    testimonials_list = Testimonial.objects.all()
    context = {'testimonials': testimonials_list}
    return render(request, 'content/testimonials.html', context)
