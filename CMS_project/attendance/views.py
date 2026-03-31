from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Q, Count, Avg
from django.core.paginator import Paginator
from django.utils import timezone
from datetime import datetime, timedelta

from .models import Attendance, AttendanceRecord, AttendanceSummary, AttendanceLeave
from courses.models import Course, CourseEnrollment
from teachers.models import Teacher
from students.models import Student, Semester
from core.views import log_activity


def is_admin(user):
    return user.is_superuser or user.is_staff


def is_teacher_or_admin(user):
    return user.is_superuser or user.is_staff or hasattr(user, 'teacher')


def is_teacher(user):
    return user.is_authenticated and (hasattr(user, 'teacher') or user.is_staff or user.is_superuser)


def is_student(user):
    return user.is_authenticated and hasattr(user, 'student')


@login_required
@user_passes_test(is_teacher_or_admin)
def attendance_list(request):
    """List all attendance sessions"""
    user = request.user
    
    if user.is_superuser or user.is_staff:
        sessions = Attendance.objects.select_related('course', 'teacher', 'semester').all()
    else:
        sessions = Attendance.objects.filter(teacher=user.teacher).select_related('course', 'semester')
    
    # Filters
    course = request.GET.get('course', '')
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    status = request.GET.get('status', '')
    
    if course:
        sessions = sessions.filter(course_id=course)
    if date_from:
        sessions = sessions.filter(date__gte=date_from)
    if date_to:
        sessions = sessions.filter(date__lte=date_to)
    if status:
        sessions = sessions.filter(status=status)
    
    courses = Course.objects.filter(status='active')
    
    paginator = Paginator(sessions, 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_title': 'Attendance Sessions',
        'sessions': page_obj,
        'courses': courses,
        'subjects': courses,  # Alias for template
        'selected_course': course,
        'selected_status': status,
    }
    return render(request, 'attendance/attendance_list.html', context)


@login_required
@user_passes_test(is_teacher_or_admin)
def attendance_create(request):
    """Create a new attendance session"""
    if request.method == 'POST':
        try:
            attendance = Attendance(
                course_id=request.POST.get('course'),
                teacher_id=request.POST.get('teacher') or (request.user.teacher.id if hasattr(request.user, 'teacher') else None),
                semester_id=request.POST.get('semester'),
                date=request.POST.get('date'),
                start_time=request.POST.get('start_time'),
                end_time=request.POST.get('end_time'),
                topic=request.POST.get('topic', ''),
                notes=request.POST.get('notes', ''),
                is_mandatory='is_mandatory' in request.POST,
            )
            attendance.save()
            
            log_activity(request.user, 'create', 'attendance', 'Attendance', attendance.id, str(attendance), request=request)
            messages.success(request, 'Attendance session created successfully!')
            return redirect('attendance:attendance_mark', pk=attendance.pk)
        except Exception as e:
            messages.error(request, f'Error creating attendance: {str(e)}')
    
    # Filter courses based on user
    if hasattr(request.user, 'teacher'):
        courses = Course.objects.filter(teacher=request.user.teacher, status='active')
    else:
        courses = Course.objects.filter(status='active')
    
    teachers = Teacher.objects.filter(status='active')
    semesters = Semester.objects.filter(is_active=True)
    
    context = {
        'page_title': 'Create Attendance Session',
        'courses': courses,
        'teachers': teachers,
        'semesters': semesters,
    }
    return render(request, 'attendance/attendance_form.html', context)


@login_required
@user_passes_test(is_teacher_or_admin)
def attendance_detail(request, pk):
    """View attendance session details"""
    attendance = get_object_or_404(Attendance, pk=pk)
    records = attendance.records.select_related('student').all()
    
    context = {
        'page_title': f'Attendance - {attendance.course} ({attendance.date})',
        'attendance': attendance,
        'records': records,
    }
    return render(request, 'attendance/attendance_detail.html', context)


@login_required
@user_passes_test(is_teacher_or_admin)
def attendance_update(request, pk):
    """Update an attendance session"""
    attendance = get_object_or_404(Attendance, pk=pk)
    
    if request.method == 'POST':
        try:
            attendance.date = request.POST.get('date')
            attendance.start_time = request.POST.get('start_time')
            attendance.end_time = request.POST.get('end_time')
            attendance.topic = request.POST.get('topic', '')
            attendance.notes = request.POST.get('notes', '')
            attendance.status = request.POST.get('status', 'scheduled')
            attendance.is_mandatory = 'is_mandatory' in request.POST
            attendance.save()
            
            log_activity(request.user, 'update', 'attendance', 'Attendance', attendance.id, str(attendance), request=request)
            messages.success(request, 'Attendance session updated successfully!')
            return redirect('attendance:attendance_detail', pk=pk)
        except Exception as e:
            messages.error(request, f'Error updating attendance: {str(e)}')
    
    context = {
        'page_title': 'Edit Attendance Session',
        'attendance': attendance,
    }
    return render(request, 'attendance/attendance_form.html', context)


@login_required
@user_passes_test(is_admin)
def attendance_delete(request, pk):
    """Delete an attendance session"""
    attendance = get_object_or_404(Attendance, pk=pk)
    
    if request.method == 'POST':
        attendance.delete()
        log_activity(request.user, 'delete', 'attendance', 'Attendance', pk, str(attendance), request=request)
        messages.success(request, 'Attendance session deleted successfully!')
        return redirect('attendance:attendance_list')
    
    context = {
        'page_title': 'Delete Attendance Session',
        'attendance': attendance,
    }
    return render(request, 'attendance/attendance_confirm_delete.html', context)


@login_required
@user_passes_test(is_teacher_or_admin)
def attendance_mark(request, pk):
    """Mark attendance for a session"""
    attendance = get_object_or_404(Attendance, pk=pk)
    
    # Get enrolled students
    enrolled_students = CourseEnrollment.objects.filter(
        course=attendance.course,
        semester=attendance.semester,
        is_active=True
    ).select_related('student')
    
    if request.method == 'POST':
        try:
            student_ids = request.POST.getlist('student')
            statuses = request.POST.getlist('status')
            
            for i, student_id in enumerate(student_ids):
                status = statuses[i] if i < len(statuses) else 'absent'
                
                record, created = AttendanceRecord.objects.update_or_create(
                    attendance=attendance,
                    student_id=student_id,
                    defaults={
                        'status': status,
                        'marked_by': request.user.teacher if hasattr(request.user, 'teacher') else None,
                    }
                )
            
            attendance.status = 'completed'
            attendance.save()
            
            messages.success(request, 'Attendance marked successfully!')
            return redirect('attendance:attendance_detail', pk=pk)
        except Exception as e:
            messages.error(request, f'Error marking attendance: {str(e)}')
    
    # Get existing records
    existing_records = {r.student_id: r.status for r in attendance.records.all()}
    
    context = {
        'page_title': f'Mark Attendance - {attendance.course} ({attendance.date})',
        'attendance': attendance,
        'enrolled_students': enrolled_students,
        'existing_records': existing_records,
    }
    return render(request, 'attendance/attendance_mark.html', context)


@login_required
@user_passes_test(is_teacher_or_admin)
def attendance_mark_all(request, pk):
    """Mark all students as present"""
    attendance = get_object_or_404(Attendance, pk=pk)
    
    if request.method == 'POST':
        try:
            enrolled_students = CourseEnrollment.objects.filter(
                course=attendance.course,
                semester=attendance.semester,
                is_active=True
            )
            
            for enrollment in enrolled_students:
                record, created = AttendanceRecord.objects.update_or_create(
                    attendance=attendance,
                    student=enrollment.student,
                    defaults={
                        'status': 'present',
                        'marked_by': request.user.teacher if hasattr(request.user, 'teacher') else None,
                    }
                )
            
            attendance.status = 'completed'
            attendance.save()
            
            messages.success(request, 'All students marked as present!')
            return redirect('attendance:attendance_detail', pk=pk)
        except Exception as e:
            messages.error(request, f'Error marking attendance: {str(e)}')
    
    return redirect('attendance:attendance_mark', pk=pk)


@login_required
@user_passes_test(is_teacher_or_admin)
def record_update(request, pk):
    """Update an attendance record"""
    record = get_object_or_404(AttendanceRecord, pk=pk)
    
    if request.method == 'POST':
        try:
            record.status = request.POST.get('status')
            record.reason = request.POST.get('reason', '')
            record.save()
            
            messages.success(request, 'Record updated successfully!')
            return redirect('attendance:attendance_detail', pk=record.attendance.pk)
        except Exception as e:
            messages.error(request, f'Error updating record: {str(e)}')
    
    context = {
        'page_title': 'Update Attendance Record',
        'record': record,
    }
    return render(request, 'attendance/record_form.html', context)


@login_required
@user_passes_test(is_student)
def student_attendance(request):
    """View student's own attendance"""
    student = request.user.student
    
    # Get all attendance records for this student
    records = AttendanceRecord.objects.filter(student=student).select_related(
        'attendance__course'
    ).order_by('-attendance__date')[:50]
    
    # Calculate statistics
    total = records.count()
    present = records.filter(status__in=['present', 'late']).count()
    absent = records.filter(status='absent').count()
    percentage = round((present / total * 100), 1) if total > 0 else 0
    
    context = {
        'page_title': 'My Attendance',
        'records': records,
        'total': total,
        'present': present,
        'absent': absent,
        'percentage': percentage,
    }
    return render(request, 'attendance/student_attendance.html', context)


@login_required
@user_passes_test(is_student)
def student_attendance_report(request):
    """View student's attendance report"""
    student = request.user.student
    
    # Get semester filter
    semester_id = request.GET.get('semester', '')
    
    records = AttendanceRecord.objects.filter(student=student)
    
    if semester_id:
        records = records.filter(attendance__semester_id=semester_id)
    
    records = records.select_related('attendance__course', 'attendance__semester').order_by('-attendance__date')
    
    semesters = Semester.objects.filter(is_active=True)
    
    context = {
        'page_title': 'Attendance Report',
        'records': records,
        'semesters': semesters,
        'selected_semester': semester_id,
    }
    return render(request, 'attendance/student_attendance_report.html', context)


# Leave/Excuse Views
@login_required
@user_passes_test(is_teacher_or_admin)
def leave_list(request):
    """List all leave applications"""
    leaves = AttendanceLeave.objects.select_related('student').all()
    
    status = request.GET.get('status', '')
    if status:
        leaves = leaves.filter(status=status)
    
    context = {
        'page_title': 'Attendance Leave Applications',
        'leaves': leaves,
        'selected_status': status,
    }
    return render(request, 'attendance/leave_list.html', context)


@login_required
@user_passes_test(is_student)
def leave_apply(request):
    """Apply for attendance leave"""
    if request.method == 'POST':
        try:
            leave = AttendanceLeave(
                student=request.user.student,
                leave_type=request.POST.get('leave_type'),
                start_date=request.POST.get('start_date'),
                end_date=request.POST.get('end_date'),
                reason=request.POST.get('reason'),
            )
            
            if request.FILES.get('attachment'):
                leave.attachment = request.FILES.get('attachment')
            
            leave.save()
            
            messages.success(request, 'Leave application submitted successfully!')
            return redirect('attendance:leave_detail', pk=leave.pk)
        except Exception as e:
            messages.error(request, f'Error submitting application: {str(e)}')
    
    context = {
        'page_title': 'Apply for Leave',
    }
    return render(request, 'attendance/leave_form.html', context)


@login_required
@user_passes_test(is_teacher_or_admin)
def leave_detail(request, pk):
    """View leave application details"""
    leave = get_object_or_404(AttendanceLeave, pk=pk)
    
    context = {
        'page_title': 'Leave Application Details',
        'leave': leave,
    }
    return render(request, 'attendance/leave_detail.html', context)


@login_required
@user_passes_test(is_admin)
def leave_approve(request, pk):
    """Approve a leave application"""
    leave = get_object_or_404(AttendanceLeave, pk=pk)
    
    if request.method == 'POST':
        leave.status = 'approved'
        leave.approved_by = request.user.teacher if hasattr(request.user, 'teacher') else None
        leave.approved_date = timezone.now()
        leave.save()
        
        messages.success(request, 'Leave application approved!')
        return redirect('attendance:leave_detail', pk=pk)
    
    context = {
        'page_title': 'Approve Leave Application',
        'leave': leave,
    }
    return render(request, 'attendance/leave_approve.html', context)


@login_required
@user_passes_test(is_admin)
def leave_reject(request, pk):
    """Reject a leave application"""
    leave = get_object_or_404(AttendanceLeave, pk=pk)
    
    if request.method == 'POST':
        leave.status = 'rejected'
        leave.approved_by = request.user.teacher if hasattr(request.user, 'teacher') else None
        leave.approved_date = timezone.now()
        leave.rejection_reason = request.POST.get('rejection_reason', '')
        leave.save()
        
        messages.success(request, 'Leave application rejected!')
        return redirect('attendance:leave_detail', pk=pk)
    
    context = {
        'page_title': 'Reject Leave Application',
        'leave': leave,
    }
    return render(request, 'attendance/leave_reject.html', context)


@login_required
@user_passes_test(is_admin)
def attendance_summary(request):
    """View attendance summary statistics"""
    # Overall statistics
    total_records = AttendanceRecord.objects.count()
    present_count = AttendanceRecord.objects.filter(status__in=['present', 'late']).count()
    absent_count = AttendanceRecord.objects.filter(status='absent').count()
    percentage = round((present_count / total_records * 100), 1) if total_records > 0 else 0
    
    # By course
    course_stats = []
    courses = Course.objects.filter(status='active')[:10]
    for course in courses:
        records = AttendanceRecord.objects.filter(attendance__course=course)
        total = records.count()
        present = records.filter(status__in=['present', 'late']).count()
        course_stats.append({
            'course': course,
            'total': total,
            'present': present,
            'percentage': round((present / total * 100), 1) if total > 0 else 0,
        })
    
    # Recent sessions
    recent_sessions = Attendance.objects.order_by('-date', '-start_time')[:10]
    
    context = {
        'page_title': 'Attendance Summary',
        'total_records': total_records,
        'present_count': present_count,
        'absent_count': absent_count,
        'percentage': percentage,
        'course_stats': course_stats,
        'recent_sessions': recent_sessions,
    }
    return render(request, 'attendance/attendance_summary.html', context)
