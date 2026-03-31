from django.contrib import admin
from .models import (
    Grade, Exam, Result, ResultBulkUpload, SemesterResult,
    Assessment, AssessmentScore
)


@admin.register(Grade)
class GradeAdmin(admin.ModelAdmin):
    list_display = ['grade', 'min_score', 'max_score', 'grade_point', 'is_passing']
    list_filter = ['is_passing']
    search_fields = ['grade', 'description']


@admin.register(Exam)
class ExamAdmin(admin.ModelAdmin):
    list_display = ['course', 'title', 'exam_type', 'date', 'total_marks', 'status']
    list_filter = ['exam_type', 'status', 'course', 'date', 'is_published']
    search_fields = ['title', 'course__code', 'course__name']
    readonly_fields = ['created_at', 'updated_at', 'duration_hours']


@admin.register(Result)
class ResultAdmin(admin.ModelAdmin):
    list_display = ['student', 'course', 'semester', 'ca_score', 'exam_score', 
                   'total_score', 'letter_grade', 'status']
    list_filter = ['status', 'is_passed', 'is_repeat', 'semester', 'letter_grade']
    search_fields = ['student__first_name', 'student__last_name', 'student__student_id',
                    'course__code', 'course__name']
    readonly_fields = ['created_at', 'updated_at', 'submitted_at', 'published_at']


@admin.register(ResultBulkUpload)
class ResultBulkUploadAdmin(admin.ModelAdmin):
    list_display = ['semester', 'course', 'total_records', 'successful_records', 
                   'failed_records', 'is_processed', 'created_at']
    list_filter = ['is_processed', 'created_at']
    readonly_fields = ['created_at', 'processed_at']


@admin.register(SemesterResult)
class SemesterResultAdmin(admin.ModelAdmin):
    list_display = ['student', 'semester', 'total_courses', 'gpa', 'cgpa', 
                   'class_rank', 'is_complete']
    list_filter = ['semester', 'is_complete', 'status']
    search_fields = ['student__first_name', 'student__last_name', 'student__student_id']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(Assessment)
class AssessmentAdmin(admin.ModelAdmin):
    list_display = ['course', 'title', 'assessment_type', 'date', 'total_marks', 'weight']
    list_filter = ['assessment_type', 'is_published', 'course']
    search_fields = ['title', 'course__code', 'course__name']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(AssessmentScore)
class AssessmentScoreAdmin(admin.ModelAdmin):
    list_display = ['assessment', 'student', 'score', 'is_submitted', 'submitted_at']
    list_filter = ['is_submitted', 'assessment__assessment_type']
    search_fields = ['student__first_name', 'student__last_name', 'student__student_id']
    readonly_fields = ['created_at', 'updated_at']
