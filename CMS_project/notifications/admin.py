from django.contrib import admin
from .models import (
    Notification, UserNotification, Message, Announcement,
    EmailTemplate, EmailLog, SMSLog, PushNotification
)


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ['title', 'notification_type', 'target_type', 'priority', 
                   'is_active', 'is_published', 'view_count', 'created_at']
    list_filter = ['notification_type', 'target_type', 'priority', 'is_active', 'is_published']
    search_fields = ['title', 'message']
    readonly_fields = ['view_count', 'click_count', 'created_at', 'updated_at', 'published_at']


@admin.register(UserNotification)
class UserNotificationAdmin(admin.ModelAdmin):
    list_display = ['user', 'notification', 'status', 'is_in_app', 'is_email_sent', 'created_at']
    list_filter = ['status', 'is_in_app', 'is_email_sent', 'is_sms_sent']
    search_fields = ['user__username', 'notification__title']
    readonly_fields = ['created_at']


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ['sender', 'recipient', 'subject', 'status', 'is_urgent', 'is_starred', 'sent_at']
    list_filter = ['status', 'is_urgent', 'is_starred']
    search_fields = ['sender__username', 'recipient__username', 'subject', 'body']
    readonly_fields = ['sent_at', 'delivered_at', 'read_at']


@admin.register(Announcement)
class AnnouncementAdmin(admin.ModelAdmin):
    list_display = ['title', 'announcement_type', 'department', 'is_featured', 
                   'is_pinned', 'is_published', 'created_at']
    list_filter = ['announcement_type', 'is_featured', 'is_pinned', 'is_published', 'department']
    search_fields = ['title', 'content']
    readonly_fields = ['created_at', 'updated_at', 'published_at']


@admin.register(EmailTemplate)
class EmailTemplateAdmin(admin.ModelAdmin):
    list_display = ['name', 'template_type', 'subject', 'is_active', 'created_at']
    list_filter = ['template_type', 'is_active']
    search_fields = ['name', 'subject']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(EmailLog)
class EmailLogAdmin(admin.ModelAdmin):
    list_display = ['recipient', 'subject', 'template', 'status', 'sent_by', 'sent_at']
    list_filter = ['status', 'sent_at']
    search_fields = ['recipient', 'subject']
    readonly_fields = ['created_at']


@admin.register(SMSLog)
class SMSLogAdmin(admin.ModelAdmin):
    list_display = ['recipient_phone', 'message', 'status', 'sent_by', 'sent_at']
    list_filter = ['status', 'sent_at']
    search_fields = ['recipient_phone', 'message']
    readonly_fields = ['created_at']


@admin.register(PushNotification)
class PushNotificationAdmin(admin.ModelAdmin):
    list_display = ['title', 'platform', 'user', 'status', 'scheduled_at', 'created_at']
    list_filter = ['platform', 'status', 'scheduled_at']
    search_fields = ['title', 'message']
    readonly_fields = ['created_at', 'sent_at']
