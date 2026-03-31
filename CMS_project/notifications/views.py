from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.db.models import Q
from django.contrib.auth.models import User
from django.utils import timezone

from .models import Notification, UserNotification, Announcement, Message
from courses.models import Department
from students.models import Semester
from core.views import log_activity


def is_admin(user):
    return user.is_superuser or user.is_staff


# Notification Views
@login_required
@user_passes_test(is_admin)
def notification_list(request):
    """List all notifications"""
    notifications = Notification.objects.all()
    announcements = Announcement.objects.filter(is_active=True).order_by('-created_at')[:20]
    messages = Message.objects.all().order_by('-sent_at')[:20]
    user_notifications = UserNotification.objects.filter(user=request.user).order_by('-created_at')[:20]
    
    context = {
        'page_title': 'Notifications',
        'notifications': notifications,
        'announcements': announcements,
        'messages': messages,
        'all_messages': messages,
        'user_notifications': user_notifications,
    }
    return render(request, 'notifications/notification_list.html', context)


@login_required
@user_passes_test(is_admin)
def notification_create(request):
    """Create a new notification"""
    if request.method == 'POST':
        try:
            notification = Notification(
                title=request.POST.get('title'),
                message=request.POST.get('message'),
                notification_type=request.POST.get('notification_type', 'info'),
                target_type=request.POST.get('target_type', 'all'),
                department_id=request.POST.get('department') or None,
                semester_id=request.POST.get('semester') or None,
                priority=request.POST.get('priority', 'medium'),
                is_published='is_published' in request.POST,
                created_by=request.user,
            )
            notification.save()
            
            # Add target users
            user_ids = request.POST.getlist('target_users')
            if user_ids:
                notification.target_users.set(user_ids)
            
            messages.success(request, 'Notification created successfully!')
            return redirect('notifications:notification_detail', pk=notification.pk)
        except Exception as e:
            messages.error(request, f'Error creating notification: {str(e)}')
    
    departments = Department.objects.filter(is_active=True)
    semesters = Semester.objects.filter(is_active=True)
    users = User.objects.filter(is_active=True)
    
    context = {
        'page_title': 'Create Notification',
        'departments': departments,
        'semesters': semesters,
        'users': users,
    }
    return render(request, 'notifications/notification_form.html', context)


@login_required
@user_passes_test(is_admin)
def notification_detail(request, pk):
    """View notification details"""
    notification = get_object_or_404(Notification, pk=pk)
    
    context = {
        'page_title': notification.title,
        'notification': notification,
    }
    return render(request, 'notifications/notification_detail.html', context)


@login_required
@user_passes_test(is_admin)
def notification_update(request, pk):
    """Update a notification"""
    notification = get_object_or_404(Notification, pk=pk)
    
    if request.method == 'POST':
        try:
            notification.title = request.POST.get('title')
            notification.message = request.POST.get('message')
            notification.notification_type = request.POST.get('notification_type', 'info')
            notification.target_type = request.POST.get('target_type', 'all')
            notification.department_id = request.POST.get('department') or None
            notification.semester_id = request.POST.get('semester') or None
            notification.priority = request.POST.get('priority', 'medium')
            notification.is_published = 'is_published' in request.POST
            notification.save()
            
            messages.success(request, 'Notification updated successfully!')
            return redirect('notifications:notification_detail', pk=pk)
        except Exception as e:
            messages.error(request, f'Error updating notification: {str(e)}')
    
    departments = Department.objects.filter(is_active=True)
    semesters = Semester.objects.filter(is_active=True)
    
    context = {
        'page_title': f'Edit {notification.title}',
        'notification': notification,
        'departments': departments,
        'semesters': semesters,
    }
    return render(request, 'notifications/notification_form.html', context)


@login_required
@user_passes_test(is_admin)
def notification_delete(request, pk):
    """Delete a notification"""
    notification = get_object_or_404(Notification, pk=pk)
    
    if request.method == 'POST':
        notification.delete()
        messages.success(request, 'Notification deleted successfully!')
        return redirect('notifications:notification_list')
    
    context = {
        'page_title': 'Delete Notification',
        'notification': notification,
    }
    return render(request, 'notifications/notification_confirm_delete.html', context)


# Announcement Views
@login_required
@user_passes_test(is_admin)
def announcement_list(request):
    """List all announcements"""
    announcements = Announcement.objects.all()
    
    context = {
        'page_title': 'Announcements',
        'announcements': announcements,
    }
    return render(request, 'notifications/announcement_list.html', context)


@login_required
@user_passes_test(is_admin)
def announcement_create(request):
    """Create a new announcement"""
    if request.method == 'POST':
        try:
            announcement = Announcement(
                title=request.POST.get('title'),
                content=request.POST.get('content'),
                announcement_type=request.POST.get('announcement_type'),
                department_id=request.POST.get('department') or None,
                semester_id=request.POST.get('semester') or None,
                level=request.POST.get('level', ''),
                contact_person=request.POST.get('contact_person', ''),
                contact_email=request.POST.get('contact_email', ''),
                contact_phone=request.POST.get('contact_phone', ''),
                is_featured='is_featured' in request.POST,
                is_pinned='is_pinned' in request.POST,
                is_draft='is_draft' not in request.POST,
                created_by=request.user,
            )
            
            if request.FILES.get('image'):
                announcement.image = request.FILES.get('image')
            
            announcement.save()
            
            messages.success(request, 'Announcement created successfully!')
            return redirect('notifications:announcement_detail', pk=announcement.pk)
        except Exception as e:
            messages.error(request, f'Error creating announcement: {str(e)}')
    
    departments = Department.objects.filter(is_active=True)
    semesters = Semester.objects.filter(is_active=True)
    
    context = {
        'page_title': 'Create Announcement',
        'departments': departments,
        'semesters': semesters,
    }
    return render(request, 'notifications/announcement_form.html', context)


@login_required
@user_passes_test(is_admin)
def announcement_detail(request, pk):
    """View announcement details"""
    announcement = get_object_or_404(Announcement, pk=pk)
    
    context = {
        'page_title': announcement.title,
        'announcement': announcement,
    }
    return render(request, 'notifications/announcement_detail.html', context)


@login_required
@user_passes_test(is_admin)
def announcement_update(request, pk):
    """Update an announcement"""
    announcement = get_object_or_404(Announcement, pk=pk)
    
    if request.method == 'POST':
        try:
            announcement.title = request.POST.get('title')
            announcement.content = request.POST.get('content')
            announcement.announcement_type = request.POST.get('announcement_type')
            announcement.department_id = request.POST.get('department') or None
            announcement.semester_id = request.POST.get('semester') or None
            announcement.level = request.POST.get('level', '')
            announcement.contact_person = request.POST.get('contact_person', '')
            announcement.contact_email = request.POST.get('contact_email', '')
            announcement.contact_phone = request.POST.get('contact_phone', '')
            announcement.is_featured = 'is_featured' in request.POST
            announcement.is_pinned = 'is_pinned' in request.POST
            announcement.is_draft = 'is_draft' not in request.POST
            
            if request.FILES.get('image'):
                announcement.image = request.FILES.get('image')
            
            announcement.save()
            
            messages.success(request, 'Announcement updated successfully!')
            return redirect('notifications:announcement_detail', pk=pk)
        except Exception as e:
            messages.error(request, f'Error updating announcement: {str(e)}')
    
    departments = Department.objects.filter(is_active=True)
    semesters = Semester.objects.filter(is_active=True)
    
    context = {
        'page_title': f'Edit {announcement.title}',
        'announcement': announcement,
        'departments': departments,
        'semesters': semesters,
    }
    return render(request, 'notifications/announcement_form.html', context)


# Message Views
@login_required
def message_list(request):
    """List messages"""
    messages_list = Message.objects.filter(
        Q(sender=request.user) | Q(recipient=request.user)
    ).exclude(
        Q(is_deleted_by_sender=True, recipient=request.user) |
        Q(is_deleted_by_recipient=True, sender=request.user)
    ).order_by('-sent_at')
    
    # Unread count
    unread_count = Message.objects.filter(recipient=request.user, status='sent').count()
    
    context = {
        'page_title': 'Messages',
        'messages': messages_list,
        'unread_count': unread_count,
    }
    return render(request, 'notifications/message_list.html', context)


@login_required
def message_send(request):
    """Send a message"""
    if request.method == 'POST':
        try:
            recipient_id = request.POST.get('recipient')
            subject = request.POST.get('subject', '')
            body = request.POST.get('body')
            is_urgent = 'is_urgent' in request.POST
            
            message = Message(
                sender=request.user,
                recipient_id=recipient_id,
                subject=subject,
                body=body,
                is_urgent=is_urgent,
            )
            
            if request.FILES.get('attachments'):
                message.attachments = request.FILES.get('attachments')
            
            message.save()
            
            messages.success(request, 'Message sent successfully!')
            return redirect('notifications:message_detail', pk=message.pk)
        except Exception as e:
            messages.error(request, f'Error sending message: {str(e)}')
    
    users = User.objects.filter(is_active=True).exclude(pk=request.user.pk)
    context = {
        'page_title': 'Send Message',
        'users': users,
    }
    return render(request, 'notifications/message_form.html', context)


@login_required
def message_detail(request, pk):
    """View message details"""
    message = get_object_or_404(Message, pk=pk)
    
    # Check permission
    if message.sender != request.user and message.recipient != request.user:
        messages.error(request, 'You do not have permission to view this message.')
        return redirect('notifications:message_list')
    
    # Mark as read
    if message.recipient == request.user and message.status == 'sent':
        message.status = 'delivered'
        message.delivered_at = timezone.now()
        message.read_at = timezone.now()
        message.save()
    
    context = {
        'page_title': message.subject or message.body[:50],
        'message': message,
    }
    return render(request, 'notifications/message_detail.html', context)


# User Notification Views
@login_required
def my_notifications(request):
    """View user's notifications"""
    notifications = UserNotification.objects.filter(
        user=request.user
    ).select_related('notification').order_by('-created_at')[:50]
    
    unread_count = UserNotification.objects.filter(user=request.user, status='unread').count()
    
    context = {
        'page_title': 'My Notifications',
        'notifications': notifications,
        'unread_count': unread_count,
    }
    return render(request, 'notifications/my_notifications.html', context)


@login_required
def mark_read(request, pk):
    """Mark a notification as read"""
    user_notification = get_object_or_404(UserNotification, pk=pk, user=request.user)
    
    user_notification.status = 'read'
    user_notification.read_at = timezone.now()
    user_notification.save()
    
    return redirect('notifications:my_notifications')


@login_required
def mark_all_read(request):
    """Mark all notifications as read"""
    UserNotification.objects.filter(user=request.user, status='unread').update(
        status='read',
        read_at=timezone.now()
    )
    
    messages.success(request, 'All notifications marked as read!')
    return redirect('notifications:my_notifications')
