from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.db.models import Count, Sum, Avg, Q, F
from django.db.models.functions import ExtractMonth, ExtractYear
from django.core.paginator import Paginator
from django.utils import timezone
from datetime import datetime, timedelta
import json

from students.models import Student, AcademicYear, Semester
from teachers.models import Teacher
from courses.models import Course, Department, CourseEnrollment
from attendance.models import Attendance, AttendanceRecord
from results.models import Result, Grade, SemesterResult, Exam
from fees.models import Invoice, Payment, FeeCategory
from notifications.models import Notification, Announcement, UserNotification
from .models import ActivityLog, SystemSettings

# from chartjs.views.colors import COLORS


def landing_page(request):
    """Public landing page"""
    return render(request, 'layouts/landing.html', {'page_title': 'Welcome'})


def is_admin(user):
    return user.is_superuser or user.is_staff


def is_teacher(user):
    return user.is_authenticated and (
        hasattr(user, 'teacher') or user.is_staff or user.is_superuser
    )


def is_student(user):
    return user.is_authenticated and hasattr(user, 'student')


@login_required
def dashboard(request):
    """Main dashboard view with analytics"""
    user = request.user
    context = {
        'page_title': 'Dashboard',
    }
    
    if user.is_superuser or user.is_staff:
        return admin_dashboard(request)
    elif hasattr(user, 'teacher'):
        return teacher_dashboard(request)
    elif hasattr(user, 'student'):
        return student_dashboard(request)
    else:
        return render(request, 'core/dashboard_admin.html', context)


@login_required
def admin_dashboard(request):
    """Admin dashboard with comprehensive analytics"""
    today = timezone.now()
    current_year = today.year
    current_month = today.month
    
    # Student Statistics
    total_students = Student.objects.count()
    active_students = Student.objects.filter(status='active').count()
    new_students_this_month = Student.objects.filter(
        created_at__year=current_year,
        created_at__month=current_month
    ).count()
    
    # Teacher Statistics
    total_teachers = Teacher.objects.count()
    active_teachers = Teacher.objects.filter(status='active').count()
    
    # Course Statistics
    total_courses = Course.objects.count()
    active_courses = Course.objects.filter(status='active').count()
    
    # Department Statistics
    total_departments = Department.objects.count()
    
    # Attendance Statistics
    today_attendance = Attendance.objects.filter(date=today.date()).first()
    if today_attendance:
        attendance_rate = today_attendance.attendance_percentage
    else:
        attendance_rate = 0
    
    # Financial Statistics
    total_revenue = Payment.objects.filter(status='verified').aggregate(Sum('amount'))['amount__sum'] or 0
    total_invoices = Invoice.objects.count()
    pending_invoices = Invoice.objects.filter(status__in=['issued', 'partial']).count()
    overdue_invoices = Invoice.objects.filter(status='overdue').count()
    
    # Result Statistics
    total_results = Result.objects.filter(status='published').count()
    avg_score = Result.objects.filter(status='published').aggregate(Avg('total_score'))['total_score__avg'] or 0
    
    # Gender Distribution for Students
    male_students = Student.objects.filter(gender='M').count()
    female_students = Student.objects.filter(gender='F').count()
    other_students = Student.objects.filter(gender='O').count()
    
    # Students per Department
    students_per_dept = Student.objects.filter(
        department__isnull=False
    ).values('department__name').annotate(
        count=Count('id')
    ).order_by('-count')[:10]
    
    # Monthly Enrollments (Last 12 months)
    monthly_enrollments = Student.objects.filter(
        created_at__gte=timezone.now() - timedelta(days=365)
    ).annotate(
        month=ExtractMonth('created_at'),
        year=ExtractYear('created_at')
    ).values('year', 'month').annotate(count=Count('id')).order_by('year', 'month')
    
    # Revenue by Month (Last 12 months)
    monthly_revenue = Payment.objects.filter(
        status='verified',
        payment_date__gte=timezone.now() - timedelta(days=365)
    ).annotate(
        month=ExtractMonth('payment_date'),
        year=ExtractYear('payment_date')
    ).values('year', 'month').annotate(
        total=Sum('amount')
    ).order_by('year', 'month')
    
    # Grade Distribution
    grade_distribution = Grade.objects.annotate(
        student_count=Count('result')
    ).values('grade', 'min_score', 'max_score', 'student_count').order_by('min_score')
    
    # Top Performing Students
    top_students = SemesterResult.objects.filter(
        is_complete=True
    ).select_related('student').order_by('-gpa')[:10]
    
    # Recent Activities
    recent_activities = ActivityLog.objects.all()[:10]
    
    # Upcoming Events
    upcoming_exams = Exam.objects.filter(
        date__gte=today.date(),
        status='upcoming'
    ).order_by('date')[:5]
    
    # Pending Tasks
    pending_approvals = Invoice.objects.filter(status='issued')[:5]
    
    context = {
        'page_title': 'Admin Dashboard',
        # Statistics
        'total_students': total_students,
        'active_students': active_students,
        'new_students_this_month': new_students_this_month,
        'total_teachers': total_teachers,
        'active_teachers': active_teachers,
        'total_courses': total_courses,
        'active_courses': active_courses,
        'total_departments': total_departments,
        'attendance_rate': attendance_rate,
        'total_revenue': total_revenue,
        'total_invoices': total_invoices,
        'pending_invoices': pending_invoices,
        'overdue_invoices': overdue_invoices,
        'total_results': total_results,
        'avg_score': round(avg_score, 1),
        
        # Charts Data
        'gender_data': {
            'male': male_students,
            'female': female_students,
            'other': other_students,
        },
        'students_per_dept': list(students_per_dept),
        'monthly_enrollments': list(monthly_enrollments),
        'monthly_revenue': list(monthly_revenue),
        'grade_distribution': list(grade_distribution),
        
        # Lists
        'top_students': top_students,
        'recent_activities': recent_activities,
        'upcoming_exams': upcoming_exams,
        'pending_approvals': pending_approvals,
    }
    
    return render(request, 'core/dashboard_admin.html', context)


@login_required
def teacher_dashboard(request):
    """Teacher dashboard with their specific analytics"""
    user = request.user
    teacher = get_object_or_404(Teacher, user=user)
    today = timezone.now()
    
    # Teacher's Courses
    assigned_courses = Course.objects.filter(teacher=teacher)
    total_courses = assigned_courses.count()
    
    # Students in teacher's courses
    total_students = CourseEnrollment.objects.filter(
        course__teacher=teacher
    ).values('student').distinct().count()
    
    # Today's Schedule
    from timetable.models import TimetableEntry, TimeSlot
    day_name = today.strftime('%A').lower()
    today_schedule = TimetableEntry.objects.filter(
        teacher=teacher,
        day=day_name
    ).select_related('course', 'room', 'time_slot').order_by('time_slot__slot_order')
    
    # Attendance Records
    total_attendance_taken = Attendance.objects.filter(teacher=teacher).count()
    pending_attendance = Attendance.objects.filter(
        teacher=teacher,
        status='in_progress'
    ).count()
    
    # Pending Results
    pending_results = Result.objects.filter(
        course__teacher=teacher,
        status__in=['pending', 'submitted']
    ).count()
    
    # Course Performance
    course_performance = []
    for course in assigned_courses[:5]:
        avg_score = Result.objects.filter(course=course, status='published').aggregate(
            Avg('total_score')
        )['total_score__avg'] or 0
        enrolled = CourseEnrollment.objects.filter(course=course, is_active=True).count()
        course_performance.append({
            'course': course,
            'avg_score': round(avg_score, 1),
            'enrolled': enrolled
        })
    
    # Student Performance Chart Data
    students_by_score = {
        'excellent': Result.objects.filter(course__teacher=teacher, total_score__gte=80).count(),
        'good': Result.objects.filter(course__teacher=teacher, total_score__gte=60, total_score__lt=80).count(),
        'average': Result.objects.filter(course__teacher=teacher, total_score__gte=40, total_score__lt=60).count(),
        'poor': Result.objects.filter(course__teacher=teacher, total_score__lt=40).count(),
    }
    
    # Notifications
    my_notifications = UserNotification.objects.filter(
        user=user,
        status='unread'
    )[:5]
    
    context = {
        'page_title': 'Teacher Dashboard',
        'teacher': teacher,
        'total_courses': total_courses,
        'total_students': total_students,
        'today_schedule': today_schedule,
        'total_attendance_taken': total_attendance_taken,
        'pending_attendance': pending_attendance,
        'pending_results': pending_results,
        'course_performance': course_performance,
        'students_by_score': students_by_score,
        'my_notifications': my_notifications,
    }
    
    return render(request, 'core/dashboard_teacher.html', context)


@login_required
def student_dashboard(request):
    """Student dashboard with their specific analytics"""
    user = request.user
    student = get_object_or_404(Student, user=user)
    today = timezone.now()
    
    # Current Semester Info
    current_semester = student.current_semester
    
    # Enrolled Courses
    enrolled_courses = CourseEnrollment.objects.filter(
        student=student,
        is_active=True
    ).select_related('course')
    total_enrolled_courses = enrolled_courses.count()
    
    # Attendance Summary
    total_classes = AttendanceRecord.objects.filter(student=student).count()
    present_classes = AttendanceRecord.objects.filter(student=student, status__in=['present', 'late']).count()
    attendance_percentage = round((present_classes / total_classes * 100), 1) if total_classes > 0 else 0
    
    # Academic Performance
    cgpa = student.gpa  # This is a property from the model
    latest_semester_result = SemesterResult.objects.filter(
        student=student
    ).select_related('semester').order_by('-semester__academic_year', '-semester__name').first()
    
    # Fee Status
    invoice = Invoice.objects.filter(student=student).order_by('-created_at').first()
    if invoice:
        fee_balance = invoice.balance
        fee_status = invoice.status
    else:
        fee_balance = 0
        fee_status = 'No Invoice'
    
    # Today's Timetable
    from timetable.models import TimetableEntry
    day_name = today.strftime('%A').lower()
    today_classes = TimetableEntry.objects.filter(
        course__in=enrolled_courses.values_list('course', flat=True),
        day=day_name
    ).select_related('course', 'room', 'time_slot').order_by('time_slot__slot_order')
    
    # Recent Results
    recent_results = Result.objects.filter(
        student=student,
        status='published'
    ).select_related('course').order_by('-created_at')[:5]
    
    # Notifications
    my_notifications = UserNotification.objects.filter(
        user=user,
        status='unread'
    )[:5]
    
    # Upcoming Events
    upcoming_exams = Exam.objects.filter(
        semester=current_semester,
        date__gte=today.date(),
        status='upcoming'
    ).order_by('date')[:3]
    
    # Course Performance Chart Data
    course_scores = []
    for enrollment in enrolled_courses[:6]:
        result = Result.objects.filter(student=student, course=enrollment.course).first()
        if result:
            course_scores.append({
                'course': enrollment.course.code,
                'score': float(result.total_score or 0)
            })
    
    context = {
        'page_title': 'Student Dashboard',
        'student': student,
        'current_semester': current_semester,
        'total_enrolled_courses': total_enrolled_courses,
        'total_classes': total_classes,
        'present_classes': present_classes,
        'attendance_percentage': attendance_percentage,
        'cgpa': cgpa,
        'latest_semester_result': latest_semester_result,
        'fee_balance': fee_balance,
        'fee_status': fee_status,
        'today_classes': today_classes,
        'recent_results': recent_results,
        'my_notifications': my_notifications,
        'upcoming_exams': upcoming_exams,
        'course_scores': json.dumps(course_scores),
    }
    
    return render(request, 'core/dashboard_student.html', context)


@login_required
def chart_data(request):
    """API endpoint for chart data"""
    chart_type = request.GET.get('type', 'students')
    
    if chart_type == 'students':
        data = {
            'labels': ['Male', 'Female', 'Other'],
            'data': [
                Student.objects.filter(gender='M').count(),
                Student.objects.filter(gender='F').count(),
                Student.objects.filter(gender='O').count(),
            ]
        }
    elif chart_type == 'attendance':
        # Last 7 days attendance
        labels = []
        data = []
        for i in range(7):
            date = timezone.now() - timedelta(days=6-i)
            labels.append(date.strftime('%b %d'))
            attendance = Attendance.objects.filter(date=date.date()).first()
            if attendance:
                data.append(attendance.attendance_percentage)
            else:
                data.append(0)
        data = {'labels': labels, 'data': data}
    elif chart_type == 'revenue':
        # Monthly revenue for current year
        labels = []
        data = []
        for month in range(1, 13):
            total = Payment.objects.filter(
                status='verified',
                payment_date__month=month,
                payment_date__year=timezone.now().year
            ).aggregate(Sum('amount'))['amount__sum'] or 0
            labels.append(datetime(tzinfo=timezone.utc, year=timezone.now().year, month=month, day=1).strftime('%B'))
            data.append(float(total))
        data = {'labels': labels, 'data': data}
    elif chart_type == 'results':
        data = {
            'labels': ['A', 'B', 'C', 'D', 'E', 'F'],
            'data': [
                Result.objects.filter(letter_grade='A').count(),
                Result.objects.filter(letter_grade='B').count(),
                Result.objects.filter(letter_grade='C').count(),
                Result.objects.filter(letter_grade='D').count(),
                Result.objects.filter(letter_grade='E').count(),
                Result.objects.filter(total_score__lt=40).count(),
            ]
        }
    else:
        data = {'labels': [], 'data': []}
    
    return JsonResponse(data)


@login_required
def analytics(request):
    """Detailed analytics page"""
    if not (request.user.is_superuser or request.user.is_staff):
        return redirect('dashboard')
    
    context = {
        'page_title': 'Analytics',
        'total_students': Student.objects.count(),
        'total_teachers': Teacher.objects.count(),
        'total_courses': Course.objects.count(),
        'total_departments': Department.objects.count(),
        'total_revenue': Payment.objects.filter(status='verified').aggregate(Sum('amount'))['amount__sum'] or 0,
    }
    
    return render(request, 'core/analytics.html', context)


def log_activity(user, action, app_name, model_name, object_id=None, object_repr=None, changes=None, request=None):
    """Helper function to log user activities"""
    ip_address = None
    user_agent = None
    
    if request:
        ip_address = request.META.get('REMOTE_ADDR')
        user_agent = request.META.get('HTTP_USER_AGENT', '')[:500]
    
    ActivityLog.objects.create(
        user=user,
        action=action,
        app_name=app_name,
        model_name=model_name,
        object_id=str(object_id) if object_id else '',
        object_repr=str(object_repr) if object_repr else '',
        changes=json.dumps(changes) if changes else '',
        ip_address=ip_address,
        user_agent=user_agent
    )
