from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator


class SystemSettings(models.Model):
    """Model for system-wide settings"""
    site_name = models.CharField(max_length=200, default='College Management System')
    site_url = models.URLField(blank=True)
    logo = models.ImageField(upload_to='settings/', blank=True, null=True)
    favicon = models.ImageField(upload_to='settings/', blank=True, null=True)
    
    # Contact Information
    contact_email = models.EmailField(blank=True)
    contact_phone = models.CharField(max_length=20, blank=True)
    contact_address = models.TextField(blank=True)
    
    # Academic Settings
    current_session = models.CharField(max_length=50, blank=True)
    current_semester = models.CharField(max_length=20, blank=True)
    
    # System Settings
    require_email_verification = models.BooleanField(default=True)
    require_student_approval = models.BooleanField(default=True)
    allow_teacher_self_registration = models.BooleanField(default=False)
    enable_online_registration = models.BooleanField(default=True)
    
    # Fee Settings
    enable_online_payment = models.BooleanField(default=True)
    payment_gateway = models.CharField(max_length=50, blank=True)
    currency = models.CharField(max_length=10, default='NGN')
    currency_symbol = models.CharField(max_length=10, default='₦')
    
    # Attendance Settings
    attendance_threshold = models.PositiveIntegerField(
        default=75,
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    
    # Result Settings
    passing_percentage = models.PositiveIntegerField(
        default=40,
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    
    # Communication Settings
    email_host = models.CharField(max_length=200, blank=True)
    email_port = models.PositiveIntegerField(default=587)
    email_use_tls = models.BooleanField(default=True)
    email_host_user = models.CharField(max_length=200, blank=True)
    email_host_password = models.CharField(max_length=200, blank=True)
    
    # SMS Settings
    sms_gateway = models.CharField(max_length=50, blank=True)
    sms_api_key = models.CharField(max_length=200, blank=True)
    
    # Social Media
    facebook_url = models.URLField(blank=True)
    twitter_url = models.URLField(blank=True)
    instagram_url = models.URLField(blank=True)
    linkedin_url = models.URLField(blank=True)
    
    # Maintenance Mode
    is_maintenance_mode = models.BooleanField(default=False)
    maintenance_message = models.TextField(blank=True)
    
    # Meta Settings
    meta_title = models.CharField(max_length=200, blank=True)
    meta_description = models.TextField(blank=True)
    meta_keywords = models.TextField(blank=True)
    
    updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='settings_updates')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = 'System Settings'

    def __str__(self):
        return self.site_name


class ActivityLog(models.Model):
    """Model for tracking user activities"""
    ACTION_CHOICES = [
        ('create', 'Create'),
        ('update', 'Update'),
        ('delete', 'Delete'),
        ('login', 'Login'),
        ('logout', 'Logout'),
        ('view', 'View'),
        ('download', 'Download'),
        ('upload', 'Upload'),
    ]

    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='activity_logs')
    
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    app_name = models.CharField(max_length=50)
    model_name = models.CharField(max_length=100)
    
    object_id = models.CharField(max_length=100, blank=True)
    object_repr = models.CharField(max_length=200, blank=True)
    
    changes = models.TextField(blank=True)  # JSON of changes
    
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.CharField(max_length=500, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name_plural = 'Activity Logs'

    def __str__(self):
        return f"{self.user} - {self.action} - {self.model_name}"


class AuditLog(models.Model):
    """Model for detailed audit logs"""
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    username = models.CharField(max_length=150)
    
    action = models.CharField(max_length=50)
    app_label = models.CharField(max_length=100)
    model_name = models.CharField(max_length=100)
    
    object_id = models.CharField(max_length=100, blank=True)
    
    old_value = models.TextField(blank=True)
    new_value = models.TextField(blank=True)
    
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.CharField(max_length=500, blank=True)
    
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.username} - {self.action} - {self.model_name}"


class UserProfile(models.Model):
    """Extended user profile model"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    
    # Additional fields
    phone = models.CharField(max_length=20, blank=True)
    avatar = models.ImageField(upload_to='profiles/', blank=True, null=True)
    bio = models.TextField(blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    
    # Address
    address = models.TextField(blank=True)
    city = models.CharField(max_length=100, blank=True)
    state = models.CharField(max_length=100, blank=True)
    country = models.CharField(max_length=100, default='Nigeria')
    postal_code = models.CharField(max_length=20, blank=True)
    
    # Social
    facebook = models.URLField(blank=True)
    twitter = models.URLField(blank=True)
    linkedin = models.URLField(blank=True)
    
    # Preferences
    language = models.CharField(max_length=10, default='en')
    timezone = models.CharField(max_length=50, default='Africa/Lagos')
    email_notifications = models.BooleanField(default=True)
    sms_notifications = models.BooleanField(default=True)
    
    # Status
    is_verified = models.BooleanField(default=False)
    last_activity = models.DateTimeField(null=True, blank=True)
    last_login_ip = models.GenericIPAddressField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = 'User Profiles'

    def __str__(self):
        return f"{self.user.username}'s Profile"


class FAQ(models.Model):
    """Model for FAQ entries"""
    question = models.CharField(max_length=500)
    answer = models.TextField()
    
    category = models.CharField(max_length=100, blank=True)
    
    order = models.PositiveIntegerField(default=0)
    is_published = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)
    
    view_count = models.PositiveIntegerField(default=0)
    
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['order', '-created_at']

    def __str__(self):
        return self.question


class Contact(models.Model):
    """Model for contact form submissions"""
    STATUS_CHOICES = [
        ('new', 'New'),
        ('read', 'Read'),
        ('replied', 'Replied'),
        ('closed', 'Closed'),
    ]

    name = models.CharField(max_length=200)
    email = models.EmailField()
    phone = models.CharField(max_length=20, blank=True)
    
    subject = models.CharField(max_length=200)
    message = models.TextField()
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='new')
    
    replied_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='replied_contacts')
    reply_message = models.TextField(blank=True)
    replied_at = models.DateTimeField(null=True, blank=True)
    
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} - {self.subject}"


class Page(models.Model):
    """Model for static pages"""
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True)
    content = models.TextField()
    
    meta_title = models.CharField(max_length=200, blank=True)
    meta_description = models.TextField(blank=True)
    
    is_published = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)
    show_in_footer = models.BooleanField(default=False)
    
    order = models.PositiveIntegerField(default=0)
    
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_pages')
    updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='updated_pages')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['order', 'title']

    def __str__(self):
        return self.title


class Backup(models.Model):
    """Model for backup records"""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]

    backup_type = models.CharField(max_length=20, choices=[
        ('full', 'Full Backup'),
        ('partial', 'Partial Backup'),
        ('database', 'Database Only'),
        ('files', 'Files Only'),
    ])
    
    file_path = models.CharField(max_length=500, blank=True)
    file_size = models.BigIntegerField(default=0)
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    error_message = models.TextField(blank=True)
    
    scheduled = models.BooleanField(default=False)
    scheduled_at = models.DateTimeField(null=True, blank=True)
    
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_backups')
    completed_at = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.backup_type} - {self.created_at.date()} ({self.get_status_display()})"
