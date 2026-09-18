from django.urls import path
from django.views.generic import TemplateView
from . import views

app_name = 'content'

urlpatterns = [
    path('about/', views.about, name='about'),
    path('contact/', views.contact, name='contact'),
    path('faq/', views.faq, name='faq'),
    path('testimonials/', views.testimonials, name='testimonials'),
    path('terms/', TemplateView.as_view(template_name='content/terms.html'), name='terms'),
    path('privacy/', TemplateView.as_view(template_name='content/privacy.html'), name='privacy'),
]
