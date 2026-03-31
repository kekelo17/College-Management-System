from django.contrib import admin
from django.utils.html import format_html
from .models import (
    Student, Guardian, StudentDocument, StudentClass, 
    AcademicYear, Semester
)


@admin.register(AcademicYear)
class AcademicYearAdmin(admin.ModelAdmin):
    list_display = ['name', 'start_date', 'end_date', 'is_current', 'created_at']
    list_filter = ['is_current']
    search_fields = ['name']
    ordering = ['-start_date']


@admin.register(Semester)
class SemesterAdmin(admin.ModelAdmin):
    list_display = ['academic_year', 'name', 'start_date', 'end_date', 'is_active']
    list_filter = ['academic_year', 'is_active']
    search_fields = ['academic_year__name', 'name']


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ['student_id', 'full_name', 'email', 'department', 'status', 'created_at']
    list_filter = ['status', 'gender', 'department', 'current_semester__academic_year']
    search_fields = ['student_id', 'first_name', 'last_name', 'email', 'phone']
    readonly_fields = ['student_id', 'created_at', 'updated_at', 'attendance_rate', 'gpa']
    fieldsets = (
        ('Personal Information', {
            'fields': ('student_id', 'user', 'first_name', 'middle_name', 'last_name', 
                      'date_of_birth', 'gender', 'blood_group', 'passport_photo')
        }),
        ('Contact Information', {
            'fields': ('email', 'phone', 'address', 'city', 'state', 'country', 'postal_code')
        }),
        ('Academic Information', {
            'fields': ('admission_date', 'current_semester', 'department', 'status')
        }),
        ('Additional Information', {
            'fields': ('nationality', 'religion', 'state_of_origin', 'local_govt')
        }),
        ('Statistics', {
            'fields': ('attendance_rate', 'gpa', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Guardian)
class GuardianAdmin(admin.ModelAdmin):
    list_display = ['name', 'relationship', 'student', 'phone', 'is_primary']
    list_filter = ['relationship', 'is_primary']
    search_fields = ['name', 'student__first_name', 'student__last_name', 'phone']


@admin.register(StudentDocument)
class StudentDocumentAdmin(admin.ModelAdmin):
    list_display = ['student', 'document_type', 'title', 'is_verified', 'uploaded_at']
    list_filter = ['document_type', 'is_verified']
    search_fields = ['student__first_name', 'student__last_name', 'title']
    readonly_fields = ['uploaded_at']


@admin.register(StudentClass)
class StudentClassAdmin(admin.ModelAdmin):
    list_display = ['student', 'semester', 'level', 'section', 'roll_number', 'is_active']
    list_filter = ['semester', 'level', 'is_active']
    search_fields = ['student__first_name', 'student__last_name', 'roll_number']
