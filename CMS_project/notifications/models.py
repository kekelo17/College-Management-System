from django.db import models
from django.contrib.auth.models import User


class Notification(models.Model):
    """Model for general notifications"""
    NOTIFICATION_TYPE_CHOICES = [
        ('info', 'Information'),
        ('success', 'Success'),
        ('warning', 'Warning'),
        ('error', 'Error'),
        ('announcement', 'Announcement'),
        ('reminder', 'Reminder'),
    ]
    
    TARGET_TYPE_CHOICES = [
        ('all', 'All Users'),
        ('students', 'All Students'),
        ('teachers', 'All Teachers'),
        ('department', 'Department'),
        ('specific', 'Specific Users'),
    ]

    title = models.CharField(max_length=200)
    message = models.TextField()
    
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPE_CHOICES, default='info')
    target_type = models.CharField(max_length=20, choices=TARGET_TYPE_CHOICES, default='all')
    
    # For targeted notifications
    department = models.ForeignKey('courses.Department', on_delete=models.SET_NULL, null=True, blank=True, related_name='notifications')
    semester = models.ForeignKey('students.Semester', on_delete=models.SET_NULL, null=True, blank=True, related_name='notifications')
    
    # For specific users
    target_users = models.ManyToManyField(User, blank=True, related_name='targeted_notifications')
    
    # Priority and status
    priority = models.CharField(max_length=10, choices=[
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    ], default='medium')
    
    is_active = models.BooleanField(default=True)
    is_published = models.BooleanField(default=False)
    published_at = models.DateTimeField(null=True, blank=True)
    
    # Scheduling
    publish_from = models.DateTimeField(null=True, blank=True)
    publish_until = models.DateTimeField(null=True, blank=True)
    auto_expire = models.BooleanField(default=True)
    expire_at = models.DateTimeField(null=True, blank=True)
    
    # Tracking
    view_count = models.PositiveIntegerField(default=0)
    click_count = models.PositiveIntegerField(default=0)
    
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_notifications')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} ({self.get_notification_type_display()})"


class UserNotification(models.Model):
    """Model for user-specific notifications"""
    STATUS_CHOICES = [
        ('unread', 'Unread'),
        ('read', 'Read'),
        ('archived', 'Archived'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='user_notifications')
    notification = models.ForeignKey(Notification, on_delete=models.CASCADE, related_name='user_notifications')
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='unread')
    
    # For in-app notifications
    is_in_app = models.BooleanField(default=True)
    
    # For email notifications
    is_email_sent = models.BooleanField(default=False)
    email_sent_at = models.DateTimeField(null=True, blank=True)
    
    # For SMS notifications
    is_sms_sent = models.BooleanField(default=False)
    sms_sent_at = models.DateTimeField(null=True, blank=True)
    
    # Tracking
    read_at = models.DateTimeField(null=True, blank=True)
    archived_at = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['user', 'notification']
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user} - {self.notification.title}"


class Message(models.Model):
    """Model for direct messages between users"""
    STATUS_CHOICES = [
        ('sent', 'Sent'),
        ('delivered', 'Delivered'),
        ('read', 'Read'),
    ]

    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages')
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_messages')
    
    subject = models.CharField(max_length=200, blank=True)
    body = models.TextField()
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='sent')
    
    # Attachments
    attachments = models.FileField(upload_to='messages/attachments/', blank=True, null=True)
    
    # Reply tracking
    parent = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='replies')
    is_reply = models.BooleanField(default=False)
    
    # Priority
    is_urgent = models.BooleanField(default=False)
    is_starred = models.BooleanField(default=False)
    
    # Timestamps
    sent_at = models.DateTimeField(auto_now_add=True)
    delivered_at = models.DateTimeField(null=True, blank=True)
    read_at = models.DateTimeField(null=True, blank=True)
    
    # Soft delete
    is_deleted_by_sender = models.BooleanField(default=False)
    is_deleted_by_recipient = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-sent_at']

    def __str__(self):
        return f"{self.sender} to {self.recipient}: {self.subject or self.body[:50]}"


class Announcement(models.Model):
    """Model for announcements"""
    ANNOUNCEMENT_TYPE_CHOICES = [
        ('academic', 'Academic'),
        ('administrative', 'Administrative'),
        ('event', 'Event'),
        ('holiday', 'Holiday'),
        ('exam', 'Exam Notice'),
        ('fee', 'Fee Notice'),
        ('admission', 'Admission'),
        ('general', 'General'),
    ]

    title = models.CharField(max_length=200)
    content = models.TextField()
    
    announcement_type = models.CharField(max_length=20, choices=ANNOUNCEMENT_TYPE_CHOICES)
    
    # For specific groups
    department = models.ForeignKey('courses.Department', on_delete=models.SET_NULL, null=True, blank=True, related_name='announcements')
    semester = models.ForeignKey('students.Semester', on_delete=models.SET_NULL, null=True, blank=True, related_name='announcements')
    level = models.CharField(max_length=10, blank=True)
    
    # Image/featured
    image = models.ImageField(upload_to='announcements/', blank=True, null=True)
    is_featured = models.BooleanField(default=False)
    is_pinned = models.BooleanField(default=False)
    
    # Status
    is_draft = models.BooleanField(default=True)
    is_published = models.BooleanField(default=False)
    published_at = models.DateTimeField(null=True, blank=True)
    
    # Dates
    event_date = models.DateField(null=True, blank=True)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    
    # Contact info
    contact_person = models.CharField(max_length=200, blank=True)
    contact_email = models.EmailField(blank=True)
    contact_phone = models.CharField(max_length=20, blank=True)
    
    # SEO
    meta_title = models.CharField(max_length=200, blank=True)
    meta_description = models.TextField(blank=True)
    
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_announcements')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-is_pinned', '-created_at']

    def __str__(self):
        return f"{self.title} ({self.get_announcement_type_display()})"


class EmailTemplate(models.Model):
    """Model for email templates"""
    TEMPLATE_TYPE_CHOICES = [
        ('welcome', 'Welcome Email'),
        ('registration', 'Registration Confirmation'),
        ('password_reset', 'Password Reset'),
        ('fee_reminder', 'Fee Reminder'),
        ('result', 'Result Notification'),
        ('attendance', 'Attendance Alert'),
        ('announcement', 'Announcement'),
        ('newsletter', 'Newsletter'),
        ('custom', 'Custom'),
    ]

    name = models.CharField(max_length=200)
    template_type = models.CharField(max_length=20, choices=TEMPLATE_TYPE_CHOICES, unique=True)
    
    subject = models.CharField(max_length=200)
    body = models.TextField()
    
    # Template variables
    variables = models.TextField(blank=True, help_text='Comma-separated list of variables')
    
    # For specific users
    is_active = models.BooleanField(default=True)
    can_edit = models.BooleanField(default=True)
    
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_templates')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.get_template_type_display()})"


class EmailLog(models.Model):
    """Model for tracking sent emails"""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('sent', 'Sent'),
        ('failed', 'Failed'),
        ('bounced', 'Bounced'),
    ]

    recipient = models.EmailField()
    recipient_user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='email_logs')
    
    subject = models.CharField(max_length=200)
    body = models.TextField()
    
    template = models.ForeignKey(EmailTemplate, on_delete=models.SET_NULL, null=True, blank=True, related_name='logs')
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    error_message = models.TextField(blank=True)
    
    sent_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='sent_emails')
    sent_at = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"To: {self.recipient} - {self.subject}"


class SMSLog(models.Model):
    """Model for tracking sent SMS"""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('sent', 'Sent'),
        ('failed', 'Failed'),
        ('delivered', 'Delivered'),
    ]

    recipient_phone = models.CharField(max_length=20)
    recipient_user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='sms_logs')
    
    message = models.TextField()
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    error_message = models.TextField(blank=True)
    
    external_id = models.CharField(max_length=100, blank=True)
    
    sent_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='sent_sms')
    sent_at = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"To: {self.recipient_phone} - {self.message[:50]}"


class PushNotification(models.Model):
    """Model for push notifications"""
    PLATFORM_CHOICES = [
        ('web', 'Web'),
        ('android', 'Android'),
        ('ios', 'iOS'),
        ('all', 'All Platforms'),
    ]

    title = models.CharField(max_length=200)
    message = models.TextField()
    
    platform = models.CharField(max_length=10, choices=PLATFORM_CHOICES, default='all')
    
    # For specific users
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, related_name='user_push_notifications')
    user_type = models.CharField(max_length=20, blank=True)  # 'student', 'teacher'
    
    # Data payload
    data = models.JSONField(default=dict, blank=True)
    
    # Scheduling
    scheduled_at = models.DateTimeField(null=True, blank=True)
    
    status = models.CharField(max_length=20, default='pending')
    sent_at = models.DateTimeField(null=True, blank=True)
    
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='push_notifications')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} - {self.get_platform_display()}"
