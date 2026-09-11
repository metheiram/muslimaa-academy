from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from notifications.models import Notification


@login_required
def student_notifications(request):
    notifications = Notification.objects.filter(user=request.user)
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'mark_read':
            notif_id = request.POST.get('notif_id')
            if notif_id:
                Notification.objects.filter(id=notif_id, user=request.user).update(is_read=True)
        elif action == 'mark_all_read':
            notifications.filter(is_read=False).update(is_read=True)
        elif action == 'delete':
            notif_id = request.POST.get('notif_id')
            if notif_id:
                Notification.objects.filter(id=notif_id, user=request.user).delete()
        return redirect('accounts:student_notifications')
    unread_count = notifications.filter(is_read=False).count()
    context = {
        'notifications': notifications,
        'unread_count': unread_count,
        'active_page': 'notifications',
    }
    return render(request, 'accounts/student_notifications.html', context)
