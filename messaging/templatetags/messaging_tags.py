from django import template

register = template.Library()


@register.filter
def get_initials(user):
    """Get initials from user (e.g., 'Iram Mukhtar' -> 'IM')."""
    if user.first_name and user.last_name:
        return (user.first_name[0] + user.last_name[0]).upper()
    elif user.first_name:
        return user.first_name[:2].upper()
    elif user.last_name:
        return user.last_name[:2].upper()
    return user.username[:2].upper()


@register.filter
def timesince_short(value):
    """Short timesince (e.g., '5m', '2h', '3d')."""
    from django.utils import timezone
    import datetime

    if not value:
        return ''

    now = timezone.now()
    diff = now - value

    days = diff.days
    hours = diff.seconds // 3600
    minutes = (diff.seconds % 3600) // 60

    if days > 7:
        return value.strftime('%b %d')
    elif days > 0:
        return f'{days}d'
    elif hours > 0:
        return f'{hours}h'
    elif minutes > 0:
        return f'{minutes}m'
    return 'now'
