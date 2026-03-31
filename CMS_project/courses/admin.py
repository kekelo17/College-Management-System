from django.contrib import admin
from .models import (
    Department, Course, CourseEnrollment, Subject, Prerequisite
)


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'faculty', 'head', 'total_courses', 'is_active']
    list_filter = ['is_active', 'faculty']
    search_fields = ['code', 'name']
    readonly_fields = ['created_at', 'updated_at', 'total_courses', 'total_students', 'total_teachers']


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'department', 'level', 'semester', 'credit_units', 'teacher', 'status']
    list_filter = ['status', 'department', 'level', 'semester', 'course_type']
    search_fields = ['code', 'name', 'department__name']
    readonly_fields = ['created_at', 'updated_at', 'total_hours', 'enrolled_students', 'average_score']
    fieldsets = (
        ('Basic Information', {
            'fields': ('code', 'name', 'department', 'teacher', 'description')
        }),
        ('Course Details', {
            'fields': ('credit_units', 'level', 'semester', 'course_type', 'syllabus', 'objectives')
        }),
        ('Capacity & Status', {
            'fields': ('max_capacity', 'min_capacity', 'status')
        }),
        ('Contact Hours', {
            'fields': ('lecture_hours', 'practical_hours', 'tutorial_hours')
        }),
        ('Assessment', {
            'fields': ('continuous_assessment_weight', 'exam_weight', 'pass_mark')
        }),
        ('Fees', {
            'fields': ('course_fee',)
        }),
        ('Statistics', {
            'fields': ('total_hours', 'enrolled_students', 'average_score', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(CourseEnrollment)
class CourseEnrollmentAdmin(admin.ModelAdmin):
    list_display = ['student', 'course', 'semester', 'status', 'is_active', 'enrollment_date']
    list_filter = ['status', 'is_active', 'is_repeat', 'semester']
    search_fields = ['student__first_name', 'student__last_name', 'course__code', 'course__name']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'course', 'teacher', 'order', 'is_active']
    list_filter = ['is_active', 'course__department']
    search_fields = ['code', 'name', 'course__name']
    ordering = ['course', 'order', 'name']


@admin.register(Prerequisite)
class PrerequisiteAdmin(admin.ModelAdmin):
    list_display = ['course', 'prerequisite', 'is_mandatory']
    list_filter = ['is_mandatory']
    search_fields = ['course__code', 'course__name', 'prerequisite__code', 'prerequisite__name']
