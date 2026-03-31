from django.contrib import admin
from .models import (
    Teacher, TeacherQualification, TeacherExperience,
    TeacherDocument, TeacherLeave
)


@admin.register(Teacher)
class TeacherAdmin(admin.ModelAdmin):
    list_display = ['teacher_id', 'full_name', 'employee_id', 'department', 'designation', 'status']
    list_filter = ['status', 'gender', 'department', 'employment_type']
    search_fields = ['teacher_id', 'employee_id', 'first_name', 'last_name', 'email', 'phone']
    readonly_fields = ['teacher_id', 'created_at', 'updated_at', 'total_courses', 'total_students']
    fieldsets = (
        ('Personal Information', {
            'fields': ('teacher_id', 'user', 'first_name', 'middle_name', 'last_name',
                      'date_of_birth', 'gender', 'blood_group', 'passport_photo')
        }),
        ('Contact Information', {
            'fields': ('email', 'phone', 'alternative_phone', 'address', 'city', 'state', 
                      'country', 'postal_code')
        }),
        ('Professional Information', {
            'fields': ('employee_id', 'department', 'designation', 'employment_type', 'subjects')
        }),
        ('Employment Details', {
            'fields': ('date_of_joining', 'date_of_confirmation', 'salary', 'status')
        }),
        ('Additional Information', {
            'fields': ('nationality', 'state_of_origin', 'marital_status', 'spouse_name',
                      'emergency_contact', 'emergency_contact_name')
        }),
        ('Statistics', {
            'fields': ('total_courses', 'total_students', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(TeacherQualification)
class TeacherQualificationAdmin(admin.ModelAdmin):
    list_display = ['teacher', 'qualification_type', 'degree', 'institution', 'is_highest']
    list_filter = ['qualification_type', 'is_highest']
    search_fields = ['teacher__first_name', 'teacher__last_name', 'degree', 'institution']


@admin.register(TeacherExperience)
class TeacherExperienceAdmin(admin.ModelAdmin):
    list_display = ['teacher', 'organization', 'position', 'start_date', 'end_date', 'is_current']
    list_filter = ['is_current']
    search_fields = ['teacher__first_name', 'teacher__last_name', 'organization', 'position']


@admin.register(TeacherDocument)
class TeacherDocumentAdmin(admin.ModelAdmin):
    list_display = ['teacher', 'document_type', 'title', 'is_verified', 'uploaded_at']
    list_filter = ['document_type', 'is_verified']
    search_fields = ['teacher__first_name', 'teacher__last_name', 'title']


@admin.register(TeacherLeave)
class TeacherLeaveAdmin(admin.ModelAdmin):
    list_display = ['teacher', 'leave_type', 'start_date', 'end_date', 'duration', 'status']
    list_filter = ['leave_type', 'status']
    search_fields = ['teacher__first_name', 'teacher__last_name']
    readonly_fields = ['duration', 'created_at', 'updated_at']
