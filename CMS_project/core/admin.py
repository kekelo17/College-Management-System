from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from .models import (
    SystemSettings, ActivityLog, AuditLog, UserProfile,
    FAQ, Contact, Page, Backup
)


class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'Profile'


class UserAdmin(BaseUserAdmin):
    inlines = (UserProfileInline,)
    list_display = BaseUserAdmin.list_display + ()
    list_filter = BaseUserAdmin.list_filter + ('is_active',)
    fieldsets = BaseUserAdmin.fieldsets


@admin.register(SystemSettings)
class SystemSettingsAdmin(admin.ModelAdmin):
    fieldsets = (
        ('Site Information', {
            'fields': ('site_name', 'site_url', 'logo', 'favicon', 'contact_email', 
                      'contact_phone', 'contact_address')
        }),
        ('Academic Settings', {
            'fields': ('current_session', 'current_semester')
        }),
        ('System Settings', {
            'fields': ('require_email_verification', 'require_student_approval',
                      'allow_teacher_self_registration', 'enable_online_registration')
        }),
        ('Fee Settings', {
            'fields': ('enable_online_payment', 'payment_gateway', 'currency', 'currency_symbol')
        }),
        ('Attendance Settings', {
            'fields': ('attendance_threshold',)
        }),
        ('Result Settings', {
            'fields': ('passing_percentage',)
        }),
        ('Email Settings', {
            'fields': ('email_host', 'email_port', 'email_use_tls', 
                      'email_host_user', 'email_host_password'),
            'classes': ('collapse',)
        }),
        ('SMS Settings', {
            'fields': ('sms_gateway', 'sms_api_key'),
            'classes': ('collapse',)
        }),
        ('Social Media', {
            'fields': ('facebook_url', 'twitter_url', 'instagram_url', 'linkedin_url')
        }),
        ('Maintenance', {
            'fields': ('is_maintenance_mode', 'maintenance_message'),
            'classes': ('collapse',)
        }),
        ('Meta', {
            'fields': ('meta_title', 'meta_description', 'meta_keywords'),
            'classes': ('collapse',)
        }),
    )


@admin.register(ActivityLog)
class ActivityLogAdmin(admin.ModelAdmin):
    list_display = ['user', 'action', 'app_name', 'model_name', 'object_repr', 'created_at']
    list_filter = ['action', 'app_name', 'model_name', 'created_at']
    search_fields = ['user__username', 'model_name', 'object_repr']
    readonly_fields = ['user', 'action', 'app_name', 'model_name', 'object_id', 
                     'object_repr', 'changes', 'ip_address', 'user_agent', 'created_at']
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ['user', 'username', 'action', 'app_label', 'model_name', 'timestamp']
    list_filter = ['action', 'app_label', 'model_name', 'timestamp']
    search_fields = ['username', 'model_name', 'object_id']
    readonly_fields = ['user', 'username', 'action', 'app_label', 'model_name', 
                     'object_id', 'old_value', 'new_value', 'ip_address', 
                     'user_agent', 'timestamp']
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False


@admin.register(FAQ)
class FAQAdmin(admin.ModelAdmin):
    list_display = ['question', 'category', 'order', 'is_published', 'is_featured', 'view_count']
    list_filter = ['is_published', 'is_featured', 'category']
    search_fields = ['question', 'answer', 'category']
    ordering = ['order', '-created_at']


@admin.register(Contact)
class ContactAdmin(admin.ModelAdmin):
    list_display = ['name', 'email', 'subject', 'status', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['name', 'email', 'subject', 'message']
    readonly_fields = ['created_at']
    
    def save_model(self, request, obj, form, change):
        if 'reply_message' in form.changed_data:
            obj.replied_by = request.user
            from django.utils import timezone
            obj.replied_at = timezone.now()
        super().save_model(request, obj, form, change)


@admin.register(Page)
class PageAdmin(admin.ModelAdmin):
    list_display = ['title', 'slug', 'is_published', 'is_featured', 'show_in_footer', 'order']
    list_filter = ['is_published', 'is_featured', 'show_in_footer']
    search_fields = ['title', 'content', 'meta_title']
    prepopulated_fields = {'slug': ('title',)}
    readonly_fields = ['created_at', 'updated_at']
    
    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(Backup)
class BackupAdmin(admin.ModelAdmin):
    list_display = ['backup_type', 'file_size', 'status', 'scheduled', 'created_at', 'completed_at']
    list_filter = ['backup_type', 'status', 'scheduled', 'created_at']
    search_fields = ['backup_type']
    readonly_fields = ['created_at']
    
    def file_size_display(self, obj):
        if obj.file_size:
            return f"{obj.file_size / (1024*1024):.2f} MB"
        return "-"
    file_size_display.short_description = 'File Size'


# Re-register UserAdmin
admin.site.unregister(User)
admin.site.register(User, UserAdmin)
