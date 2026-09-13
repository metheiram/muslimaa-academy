from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.db.models import Q
from django.core.mail import send_mail
from django.conf import settings
from .models import Message


def _get_conversations(user):
    """Group messages into conversations (like WhatsApp chat list)."""
    all_msgs = Message.objects.filter(
        Q(sender=user) | Q(recipient=user)
    ).select_related('sender', 'recipient').order_by('-created_at')

    seen = {}
    for msg in all_msgs:
        other = msg.recipient if msg.sender == user else msg.sender
        key = other.id
        if key not in seen:
            unread = Message.objects.filter(
                sender=other, recipient=user, is_read=False
            ).count() if other != user else 0
            seen[key] = {
                'other_user': other,
                'latest_message': msg,
                'unread_count': unread,
            }

    return sorted(seen.values(), key=lambda x: x['latest_message'].created_at, reverse=True)


def _get_thread(user, other_user_id):
    """Get all messages between user and another user, ordered oldest first."""
    return Message.objects.filter(
        (Q(sender=user) & Q(recipient_id=other_user_id)) |
        (Q(sender_id=other_user_id) & Q(recipient=user))
    ).select_related('sender', 'recipient').order_by('created_at')


@login_required
def inbox(request):
    conversations = _get_conversations(request.user)
    unread_count = Message.objects.filter(recipient=request.user, is_read=False).count()

    context = {
        'conversations': conversations,
        'unread_count': unread_count,
        'active_page': 'inbox',
    }
    return render(request, 'messaging/inbox.html', context)


@login_required
def sent(request):
    sent_msgs = Message.objects.filter(
        sender=request.user
    ).select_related('recipient').order_by('-created_at')

    context = {
        'messages': sent_msgs,
        'active_page': 'sent',
    }
    return render(request, 'messaging/sent.html', context)


@login_required
def compose(request, recipient_id=None):
    if request.user.is_superuser:
        available_users = User.objects.filter(is_active=True).exclude(id=request.user.id)
    elif request.user.is_staff:
        from courses.enrollment_models import Enrollment
        assigned_student_ids = Enrollment.objects.filter(
            teacher=request.user, status='approved'
        ).values_list('student_id', flat=True).distinct()
        assigned_students = User.objects.filter(id__in=assigned_student_ids, is_active=True)
        admins = User.objects.filter(is_superuser=True)
        available_users = (assigned_students | admins).exclude(id=request.user.id).distinct()
    else:
        teachers = User.objects.filter(is_staff=True, is_active=True)
        admins = User.objects.filter(is_superuser=True)
        available_users = (teachers | admins).exclude(id=request.user.id).distinct()

    selected_recipient = None
    if recipient_id:
        selected_recipient = int(recipient_id)

    if request.method == 'POST':
        rid = request.POST.get('recipient')
        subject = request.POST.get('subject', '').strip()
        body = request.POST.get('body', '').strip()

        if not all([rid, body]):
            messages.error(request, 'Please select a recipient and type a message.')
            return redirect('messaging:compose')

        recipient_user = get_object_or_404(User, id=rid)

        Message.objects.create(
            sender=request.user,
            recipient=recipient_user,
            subject=subject or 'No Subject',
            body=body,
        )

        if recipient_user.email:
            try:
                send_mail(
                    f'New Message from {request.user.get_full_name()} | Muslimaa Academy',
                    f"Assalam-o-Alaikum {recipient_user.first_name},\n\n"
                    f"You have a new message from {request.user.get_full_name()}:\n\n"
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
        return redirect('messaging:view_message_by_user', user_id=recipient_user.id)

    context = {
        'users': available_users,
        'selected_recipient': selected_recipient,
        'active_page': 'compose',
    }
    return render(request, 'messaging/compose.html', context)


@login_required
def view_message(request, message_id):
    msg = get_object_or_404(
        Message.objects.filter(Q(sender=request.user) | Q(recipient=request.user)),
        id=message_id
    )

    if msg.recipient == request.user and not msg.is_read:
        msg.is_read = True
        msg.save()

    other_user = msg.sender if msg.sender != request.user else msg.recipient
    thread = _get_thread(request.user, other_user.id)
    conversations = _get_conversations(request.user)
    unread_count = Message.objects.filter(recipient=request.user, is_read=False).count()

    context = {
        'message': msg,
        'other_user': other_user,
        'thread': thread,
        'conversations': conversations,
        'unread_count': unread_count,
        'selected_id': msg.id,
    }
    return render(request, 'messaging/view_message.html', context)


@login_required
def view_message_by_user(request, user_id):
    """View conversation with a specific user (by user ID)."""
    other_user = get_object_or_404(User, id=user_id)

    unread_msgs = Message.objects.filter(
        sender=other_user, recipient=request.user, is_read=False
    )
    unread_msgs.update(is_read=True)

    thread = _get_thread(request.user, user_id)
    latest_msg = thread.first() if thread.exists() else None

    conversations = _get_conversations(request.user)
    unread_count = Message.objects.filter(recipient=request.user, is_read=False).count()

    context = {
        'message': latest_msg,
        'other_user': other_user,
        'thread': thread,
        'conversations': conversations,
        'unread_count': unread_count,
        'selected_id': latest_msg.id if latest_msg else None,
    }
    return render(request, 'messaging/view_message.html', context)


@login_required
def reply_message(request, message_id):
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


@login_required
def delete_message(request, message_id):
    msg = get_object_or_404(
        Message.objects.filter(Q(sender=request.user) | Q(recipient=request.user)),
        id=message_id
    )
    other_user = msg.sender if msg.sender != request.user else msg.recipient
    msg.delete()
    messages.success(request, 'Message deleted.')
    return redirect('messaging:inbox')
