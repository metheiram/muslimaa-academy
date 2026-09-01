from django.shortcuts import render, get_object_or_404
from .models import Workshop


def workshop_list(request):
    """Display all workshops."""
    workshops = Workshop.objects.filter(is_active=True)
    context = {'workshops': workshops}
    return render(request, 'workshops/workshop_list.html', context)


def workshop_detail(request, slug):
    """Display a single workshop."""
    workshop = get_object_or_404(Workshop, slug=slug, is_active=True)
    context = {'workshop': workshop}
    return render(request, 'workshops/workshop_detail.html', context)
