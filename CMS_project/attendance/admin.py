from django.contrib import admin
from .models import (
    Attendance, AttendanceRecord, AttendanceSummary, AttendanceLeave
)


@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ['course', 'date', 'start_time', 'status', 'total_students', 
                   'present_count', 'absent_count', 'attendance_percentage']
    list_filter = ['status', 'course', 'date', 'is_mandatory', 'semester']
    search_fields = ['course__code', 'course__name', 'topic']
    readonly_fields = ['created_at', 'updated_at', 'total_students', 'present_count', 
                      'absent_count', 'late_count', 'attendance_percentage']


@admin.register(AttendanceRecord)
class AttendanceRecordAdmin(admin.ModelAdmin):
    list_display = ['student', 'attendance', 'status', 'marked_by', 'marked_time', 'is_verified']
    list_filter = ['status', 'is_verified', 'is_approved', 'attendance__date']
    search_fields = ['student__first_name', 'student__last_name', 'student__student_id']
    readonly_fields = ['marked_time', 'updated_time']


@admin.register(AttendanceSummary)
class AttendanceSummaryAdmin(admin.ModelAdmin):
    list_display = ['student', 'semester', 'period_type', 'start_date', 'end_date',
                   'attendance_percentage', 'total_sessions']
    list_filter = ['period_type', 'semester']
    search_fields = ['student__first_name', 'student__last_name', 'student__student_id']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(AttendanceLeave)
class AttendanceLeaveAdmin(admin.ModelAdmin):
    list_display = ['student', 'leave_type', 'start_date', 'end_date', 'duration', 'status']
    list_filter = ['leave_type', 'status']
    search_fields = ['student__first_name', 'student__last_name', 'student__student_id']
    readonly_fields = ['duration', 'created_at', 'updated_at']
