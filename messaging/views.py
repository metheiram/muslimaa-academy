from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.db.models import Q
from django.core.mail import send_mail
from django.conf import settings
from .models import Message


@login_required
def inbox(request):
    """View received messages."""
    received = Message.objects.filter(recipient=request.user).select_related('sender')
    unread_count = received.filter(is_read=False).count()

    context = {
        'messages_list': received,
        'unread_count': unread_count,
        'active_page': 'inbox',
    }
    return render(request, 'messaging/inbox.html', context)


@login_required
def sent(request):
    """View sent messages."""
    sent_msgs = Message.objects.filter(sender=request.user).select_related('recipient')

    context = {
        'messages_list': sent_msgs,
        'active_page': 'sent',
    }
    return render(request, 'messaging/sent.html', context)


@login_required
def compose(request, recipient_id=None):
    """Compose a new message."""
    recipient = None
    if recipient_id:
        recipient = get_object_or_404(User, id=recipient_id)

    if request.user.is_superuser:
        available_users = User.objects.filter(is_active=True).exclude(id=request.user.id)
    elif request.user.is_staff:
        students = User.objects.filter(is_superuser=False, is_staff=False, is_active=True)
        admins = User.objects.filter(is_superuser=True)
        available_users = (students | admins).exclude(id=request.user.id).distinct()
    else:
        teachers = User.objects.filter(is_staff=True, is_active=True)
        admins = User.objects.filter(is_superuser=True)
        available_users = (teachers | admins).exclude(id=request.user.id).distinct()

    if request.method == 'POST':
        recipient_id = request.POST.get('recipient')
        subject = request.POST.get('subject', '').strip()
        body = request.POST.get('body', '').strip()

        if not all([recipient_id, subject, body]):
            messages.error(request, 'All fields are required.')
            return redirect('messaging:compose')

        recipient_user = get_object_or_404(User, id=recipient_id)

        Message.objects.create(
            sender=request.user,
            recipient=recipient_user,
            subject=subject,
            body=body,
        )

        if recipient_user.email:
            try:
                send_mail(
                    f'New Message: {subject} | Muslimaa Academy',
                    f"Assalam-o-Alaikum {recipient_user.first_name},\n\n"
                    f"You have a new message from {request.user.get_full_name()}:\n\n"
                    f"Subject: {subject}\n\n"
                    f"{body}\n\n"
                    f"Log in to your dashboard to reply.\n\n"
                    f"Muslimaa Academy Team",
                    settings.DEFAULT_FROM_EMAIL,
                    [recipient_user.email],
                    fail_silently=True,
                )
            except Exception:
                pass

        messages.success(request, f'Message sent to {recipient_user.get_full_name()}!')
        return redirect('messaging:sent')

    context = {
        'available_users': available_users,
        'selected_recipient': recipient,
    }
    return render(request, 'messaging/compose.html', context)


@login_required
def view_message(request, message_id):
    """View a single message."""
    msg = get_object_or_404(
        Message.objects.filter(Q(sender=request.user) | Q(recipient=request.user)),
        id=message_id
    )

    if msg.recipient == request.user and not msg.is_read:
        msg.is_read = True
        msg.save()

    context = {
        'msg': msg,
    }
    return render(request, 'messaging/view_message.html', context)


@login_required
def reply_message(request, message_id):
    """Reply to a message."""
    original = get_object_or_404(
        Message.objects.filter(Q(sender=request.user) | Q(recipient=request.user)),
        id=message_id
    )

    if request.method == 'POST':
        body = request.POST.get('body', '').strip()
        if body:
            reply_to = original.sender if original.sender != request.user else original.recipient
            Message.objects.create(
                sender=request.user,
                recipient=reply_to,
                subject=f"Re: {original.subject}",
                body=body,
            )
            messages.success(request, f'Reply sent to {reply_to.get_full_name()}!')
            return redirect('messaging:view_message', message_id=original.id)

    return redirect('messaging:view_message', message_id=original.id)


@login_required
def delete_message(request, message_id):
    """Delete a message."""
    msg = get_object_or_404(
        Message.objects.filter(Q(sender=request.user) | Q(recipient=request.user)),
        id=message_id
    )
    msg.delete()
    messages.success(request, 'Message deleted.')
    return redirect('messaging:inbox')
