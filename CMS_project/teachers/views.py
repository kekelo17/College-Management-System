from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.db.models import Q
from django.core.paginator import Paginator
from django.utils import timezone
from django.utils.dateparse import parse_date
import csv
import io

from .models import Teacher, TeacherQualification, TeacherExperience, TeacherDocument, TeacherLeave
from courses.models import Department, Course
from attendance.models import Attendance
from results.models import Result
from core.views import log_activity


def is_admin(user):
    return user.is_superuser or user.is_staff


def is_teacher_or_admin(user):
    return user.is_superuser or user.is_staff or hasattr(user, 'teacher')


@login_required
@user_passes_test(is_admin)
def teacher_list(request):
    """List all teachers with filtering and pagination"""
    query = request.GET.get('q', '')
    department = request.GET.get('department', '')
    status = request.GET.get('status', '')
    
    teachers = Teacher.objects.select_related('department').all()
    
    if query:
        teachers = teachers.filter(
            Q(teacher_id__icontains=query) |
            Q(first_name__icontains=query) |
            Q(last_name__icontains=query) |
            Q(email__icontains=query) |
            Q(phone__icontains=query) |
            Q(employee_id__icontains=query)
        )
    
    if department:
        teachers = teachers.filter(department_id=department)
    
    if status:
        teachers = teachers.filter(status=status)
    
    departments = Department.objects.filter(is_active=True)
    
    paginator = Paginator(teachers, 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_title': 'Teachers',
        'teachers': page_obj,
        'departments': departments,
        'departments_list': departments,
        'query': query,
        'selected_department': department,
        'selected_status': status,
        'designations': ['Professor', 'Associate Professor', 'Assistant Professor', 'Lecturer', 'Tutor'],
    }
    return render(request, 'teachers/teacher_list.html', context)


@login_required
@user_passes_test(is_admin)
def teacher_create(request):
    """Create a new teacher"""
    if request.method == 'POST':
        try:
            teacher = Teacher(
                first_name=request.POST.get('first_name'),
                last_name=request.POST.get('last_name'),
                middle_name=request.POST.get('middle_name', ''),
                date_of_birth=request.POST.get('date_of_birth'),
                gender=request.POST.get('gender'),
                blood_group=request.POST.get('blood_group', ''),
                email=request.POST.get('email'),
                phone=request.POST.get('phone'),
                alternative_phone=request.POST.get('alternative_phone', ''),
                address=request.POST.get('address'),
                city=request.POST.get('city'),
                state=request.POST.get('state'),
                country=request.POST.get('country', 'Nigeria'),
                postal_code=request.POST.get('postal_code', ''),
                employee_id=request.POST.get('employee_id'),
                department_id=request.POST.get('department'),
                designation=request.POST.get('designation'),
                employment_type=request.POST.get('employment_type', 'full_time'),
                date_of_joining=request.POST.get('date_of_joining'),
                salary=request.POST.get('salary') or None,
                nationality=request.POST.get('nationality', 'Nigerian'),
                state_of_origin=request.POST.get('state_of_origin', ''),
                marital_status=request.POST.get('marital_status', ''),
                spouse_name=request.POST.get('spouse_name', ''),
                emergency_contact=request.POST.get('emergency_contact', ''),
                emergency_contact_name=request.POST.get('emergency_contact_name', ''),
                status='active',
            )
            teacher.save()
            
            # Handle user creation
            username = request.POST.get('username')
            password = request.POST.get('password')
            if username and password:
                from django.contrib.auth.models import User
                user = User.objects.create_user(
                    username=username,
                    email=teacher.email,
                    password=password,
                    first_name=teacher.first_name,
                    last_name=teacher.last_name
                )
                teacher.user = user
                teacher.save()
            
            # Handle passport photo upload
            if request.FILES.get('passport_photo'):
                teacher.passport_photo = request.FILES.get('passport_photo')
                teacher.save()
            
            log_activity(request.user, 'create', 'teachers', 'Teacher', teacher.id, str(teacher), request=request)
            messages.success(request, f'Teacher {teacher.full_name} created successfully!')
            return redirect('teachers:teacher_detail', pk=teacher.pk)
        except Exception as e:
            messages.error(request, f'Error creating teacher: {str(e)}')
    
    departments = Department.objects.filter(is_active=True)
    context = {
        'page_title': 'Add Teacher',
        'departments': departments,
    }
    return render(request, 'teachers/teacher_form.html', context)


@login_required
@user_passes_test(is_admin)
def teacher_detail(request, pk):
    """View teacher details"""
    teacher = get_object_or_404(Teacher, pk=pk)
    
    # Qualifications
    qualifications = teacher.qualifications.all()
    
    # Experiences
    experiences = teacher.experiences.all()
    
    # Documents
    documents = teacher.documents.all()
    
    # Assigned courses
    courses = Course.objects.filter(teacher=teacher)
    
    # Attendance records taken
    attendance_records = Attendance.objects.filter(teacher=teacher)[:10]
    
    # Results entered
    results = Result.objects.filter(course__teacher=teacher).select_related('student', 'course')[:10]
    
    context = {
        'page_title': f'{teacher.full_name} - Teacher Details',
        'teacher': teacher,
        'qualifications': qualifications,
        'experiences': experiences,
        'documents': documents,
        'courses': courses,
        'attendance_records': attendance_records,
        'results': results,
    }
    return render(request, 'teachers/teacher_detail.html', context)


@login_required
@user_passes_test(is_admin)
def teacher_update(request, pk):
    """Update teacher details"""
    teacher = get_object_or_404(Teacher, pk=pk)
    
    if request.method == 'POST':
        try:
            teacher.first_name = request.POST.get('first_name')
            teacher.last_name = request.POST.get('last_name')
            teacher.middle_name = request.POST.get('middle_name', '')
            teacher.date_of_birth = request.POST.get('date_of_birth')
            teacher.gender = request.POST.get('gender')
            teacher.blood_group = request.POST.get('blood_group', '')
            teacher.email = request.POST.get('email')
            teacher.phone = request.POST.get('phone')
            teacher.alternative_phone = request.POST.get('alternative_phone', '')
            teacher.address = request.POST.get('address')
            teacher.city = request.POST.get('city')
            teacher.state = request.POST.get('state')
            teacher.country = request.POST.get('country', 'Nigeria')
            teacher.postal_code = request.POST.get('postal_code', '')
            teacher.employee_id = request.POST.get('employee_id')
            teacher.department_id = request.POST.get('department')
            teacher.designation = request.POST.get('designation')
            teacher.employment_type = request.POST.get('employment_type', 'full_time')
            teacher.date_of_joining = request.POST.get('date_of_joining')
            teacher.salary = request.POST.get('salary') or None
            teacher.nationality = request.POST.get('nationality', 'Nigerian')
            teacher.state_of_origin = request.POST.get('state_of_origin', '')
            teacher.marital_status = request.POST.get('marital_status', '')
            teacher.spouse_name = request.POST.get('spouse_name', '')
            teacher.emergency_contact = request.POST.get('emergency_contact', '')
            teacher.emergency_contact_name = request.POST.get('emergency_contact_name', '')
            teacher.status = request.POST.get('status', 'active')
            
            if request.FILES.get('passport_photo'):
                teacher.passport_photo = request.FILES.get('passport_photo')
            
            teacher.save()
            
            log_activity(request.user, 'update', 'teachers', 'Teacher', teacher.id, str(teacher), request=request)
            messages.success(request, f'Teacher {teacher.full_name} updated successfully!')
            return redirect('teachers:teacher_detail', pk=teacher.pk)
        except Exception as e:
            messages.error(request, f'Error updating teacher: {str(e)}')
    
    departments = Department.objects.filter(is_active=True)
    context = {
        'page_title': f'Edit {teacher.full_name}',
        'teacher': teacher,
        'departments': departments,
    }
    return render(request, 'teachers/teacher_form.html', context)


@login_required
@user_passes_test(is_admin)
def teacher_delete(request, pk):
    """Delete a teacher"""
    teacher = get_object_or_404(Teacher, pk=pk)
    
    if request.method == 'POST':
        teacher_name = teacher.full_name
        teacher.delete()
        log_activity(request.user, 'delete', 'teachers', 'Teacher', pk, teacher_name, request=request)
        messages.success(request, f'Teacher {teacher_name} deleted successfully!')
        return redirect('teachers:teacher_list')
    
    context = {
        'page_title': 'Delete Teacher',
        'teacher': teacher,
    }
    return render(request, 'teachers/teacher_confirm_delete.html', context)


@login_required
def teacher_profile(request):
    """Teacher's own profile view"""
    if not hasattr(request.user, 'teacher'):
        messages.error(request, 'You are not registered as a teacher.')
        return redirect('dashboard')
    
    teacher = request.user.teacher
    return teacher_detail(request, teacher.pk)


# Qualification Views
@login_required
@user_passes_test(is_admin)
def qualification_create(request, teacher_pk):
    """Add a qualification to a teacher"""
    teacher = get_object_or_404(Teacher, pk=teacher_pk)
    
    if request.method == 'POST':
        try:
            qualification = TeacherQualification(
                teacher=teacher,
                qualification_type=request.POST.get('qualification_type'),
                degree=request.POST.get('degree'),
                institution=request.POST.get('institution'),
                field_of_study=request.POST.get('field_of_study'),
                start_date=request.POST.get('start_date'),
                end_date=request.POST.get('end_date') or None,
                grade=request.POST.get('grade', ''),
                is_highest='is_highest' in request.POST,
            )
            
            if request.FILES.get('certificate'):
                qualification.certificate = request.FILES.get('certificate')
            
            qualification.save()
            
            messages.success(request, f'Qualification {qualification.degree} added successfully!')
            return redirect('teachers:teacher_detail', pk=teacher_pk)
        except Exception as e:
            messages.error(request, f'Error adding qualification: {str(e)}')
    
    context = {
        'page_title': f'Add Qualification for {teacher.full_name}',
        'teacher': teacher,
    }
    return render(request, 'teachers/qualification_form.html', context)


@login_required
@user_passes_test(is_admin)
def qualification_delete(request, pk):
    """Delete a qualification"""
    qualification = get_object_or_404(TeacherQualification, pk=pk)
    teacher_pk = qualification.teacher.pk
    
    if request.method == 'POST':
        qualification.delete()
        messages.success(request, 'Qualification deleted successfully!')
        return redirect('teachers:teacher_detail', pk=teacher_pk)
    
    context = {
        'page_title': 'Delete Qualification',
        'qualification': qualification,
    }
    return render(request, 'teachers/qualification_confirm_delete.html', context)


# Experience Views
@login_required
@user_passes_test(is_admin)
def experience_create(request, teacher_pk):
    """Add experience to a teacher"""
    teacher = get_object_or_404(Teacher, pk=teacher_pk)
    
    if request.method == 'POST':
        try:
            experience = TeacherExperience(
                teacher=teacher,
                organization=request.POST.get('organization'),
                position=request.POST.get('position'),
                department=request.POST.get('department', ''),
                start_date=request.POST.get('start_date'),
                end_date=request.POST.get('end_date') or None,
                is_current='is_current' in request.POST,
                responsibilities=request.POST.get('responsibilities', ''),
                salary=request.POST.get('salary') or None,
            )
            experience.save()
            
            messages.success(request, f'Experience at {experience.organization} added successfully!')
            return redirect('teachers:teacher_detail', pk=teacher_pk)
        except Exception as e:
            messages.error(request, f'Error adding experience: {str(e)}')
    
    context = {
        'page_title': f'Add Experience for {teacher.full_name}',
        'teacher': teacher,
    }
    return render(request, 'teachers/experience_form.html', context)


@login_required
@user_passes_test(is_admin)
def experience_delete(request, pk):
    """Delete an experience"""
    experience = get_object_or_404(TeacherExperience, pk=pk)
    teacher_pk = experience.teacher.pk
    
    if request.method == 'POST':
        experience.delete()
        messages.success(request, 'Experience deleted successfully!')
        return redirect('teachers:teacher_detail', pk=teacher_pk)
    
    context = {
        'page_title': 'Delete Experience',
        'experience': experience,
    }
    return render(request, 'teachers/experience_confirm_delete.html', context)


# Document Views
@login_required
@user_passes_test(is_admin)
def teacher_document_create(request, teacher_pk):
    """Add a document to a teacher"""
    teacher = get_object_or_404(Teacher, pk=teacher_pk)
    
    if request.method == 'POST':
        try:
            document = TeacherDocument(
                teacher=teacher,
                document_type=request.POST.get('document_type'),
                title=request.POST.get('title'),
                file=request.FILES.get('file'),
                issue_date=request.POST.get('issue_date') or None,
                expiry_date=request.POST.get('expiry_date') or None,
                notes=request.POST.get('notes', ''),
            )
            document.save()
            
            messages.success(request, f'Document {document.title} uploaded successfully!')
            return redirect('teachers:teacher_detail', pk=teacher_pk)
        except Exception as e:
            messages.error(request, f'Error uploading document: {str(e)}')
    
    context = {
        'page_title': f'Upload Document for {teacher.full_name}',
        'teacher': teacher,
    }
    return render(request, 'teachers/document_form.html', context)


@login_required
@user_passes_test(is_admin)
def teacher_document_delete(request, pk):
    """Delete a teacher document"""
    document = get_object_or_404(TeacherDocument, pk=pk)
    teacher_pk = document.teacher.pk
    
    if request.method == 'POST':
        document.delete()
        messages.success(request, 'Document deleted successfully!')
        return redirect('teachers:teacher_detail', pk=teacher_pk)
    
    context = {
        'page_title': 'Delete Document',
        'document': document,
    }
    return render(request, 'teachers/document_confirm_delete.html', context)


# Leave Views
@login_required
@user_passes_test(is_teacher_or_admin)
def teacher_leave_list(request):
    """List all leave applications"""
    user = request.user
    
    if user.is_superuser or user.is_staff:
        leaves = TeacherLeave.objects.select_related('teacher').all()
    else:
        leaves = TeacherLeave.objects.filter(teacher=user.teacher)
    
    status = request.GET.get('status', '')
    if status:
        leaves = leaves.filter(status=status)
    
    context = {
        'page_title': 'Leave Applications',
        'leaves': leaves,
        'selected_status': status,
    }
    return render(request, 'teachers/leave_list.html', context)


@login_required
@user_passes_test(is_teacher_or_admin)
def leave_apply(request):
    """Apply for leave"""
    if not hasattr(request.user, 'teacher'):
        messages.error(request, 'You are not registered as a teacher.')
        return redirect('dashboard')
    
    teacher = request.user.teacher
    
    if request.method == 'POST':
        try:
            leave = TeacherLeave(
                teacher=teacher,
                leave_type=request.POST.get('leave_type'),
                start_date=request.POST.get('start_date'),
                end_date=request.POST.get('end_date'),
                reason=request.POST.get('reason'),
            )
            leave.save()
            
            messages.success(request, 'Leave application submitted successfully!')
            return redirect('teachers:leave_detail', pk=leave.pk)
        except Exception as e:
            messages.error(request, f'Error submitting leave application: {str(e)}')
    
    context = {
        'page_title': 'Apply for Leave',
    }
    return render(request, 'teachers/leave_form.html', context)


@login_required
@user_passes_test(is_teacher_or_admin)
def leave_detail(request, pk):
    """View leave details"""
    leave = get_object_or_404(TeacherLeave, pk=pk)
    
    # Check permission
    if not (request.user.is_superuser or request.user.is_staff) and leave.teacher.user != request.user:
        messages.error(request, 'You do not have permission to view this leave.')
        return redirect('teachers:leave_list')
    
    context = {
        'page_title': f'Leave Application - {leave.teacher.full_name}',
        'leave': leave,
    }
    return render(request, 'teachers/leave_detail.html', context)


@login_required
@user_passes_test(is_admin)
def leave_approve(request, pk):
    """Approve a leave application"""
    leave = get_object_or_404(TeacherLeave, pk=pk)
    
    if request.method == 'POST':
        leave.status = 'approved'
        leave.approved_by = request.user
        leave.approved_date = timezone.now()
        leave.save()
        
        messages.success(request, 'Leave application approved!')
        return redirect('teachers:leave_detail', pk=pk)
    
    context = {
        'page_title': 'Approve Leave',
        'leave': leave,
    }
    return render(request, 'teachers/leave_approve.html', context)


@login_required
@user_passes_test(is_admin)
def leave_reject(request, pk):
    """Reject a leave application"""
    leave = get_object_or_404(TeacherLeave, pk=pk)
    
    if request.method == 'POST':
        leave.status = 'rejected'
        leave.approved_by = request.user
        leave.approved_date = timezone.now()
        leave.rejection_reason = request.POST.get('rejection_reason', '')
        leave.save()
        
        messages.success(request, 'Leave application rejected!')
        return redirect('teachers:leave_detail', pk=pk)
    
    context = {
        'page_title': 'Reject Leave',
        'leave': leave,
    }
    return render(request, 'teachers/leave_reject.html', context)


# Bulk Operations
@login_required
@user_passes_test(is_admin)
def teacher_import(request):
    """Import teachers from CSV"""
    if request.method == 'POST' and request.FILES.get('file'):
        try:
            csv_file = request.FILES['file']
            decoded_file = csv_file.read().decode('utf-8')
            csv_reader = csv.DictReader(io.StringIO(decoded_file))
            
            imported_count = 0
            error_count = 0
            errors = []
            
            for row in csv_reader:
                try:
                    teacher = Teacher(
                        first_name=row.get('first_name', ''),
                        last_name=row.get('last_name', ''),
                        middle_name=row.get('middle_name', ''),
                        date_of_birth=row.get('date_of_birth'),
                        gender=row.get('gender', 'M'),
                        email=row.get('email'),
                        phone=row.get('phone', ''),
                        address=row.get('address', ''),
                        city=row.get('city', ''),
                        state=row.get('state', ''),
                        country=row.get('country', 'Nigeria'),
                        employee_id=row.get('employee_id', ''),
                        designation=row.get('designation', ''),
                        employment_type=row.get('employment_type', 'full_time'),
                        date_of_joining=row.get('date_of_joining'),
                        status='active',
                    )
                    teacher.save()
                    imported_count += 1
                except Exception as e:
                    error_count += 1
                    errors.append(f"Row error: {str(e)}")
            
            messages.success(request, f'Successfully imported {imported_count} teachers. {error_count} errors.')
            if errors:
                for error in errors[:10]:
                    messages.warning(request, error)
            
            return redirect('teachers:teacher_list')
        except Exception as e:
            messages.error(request, f'Error importing teachers: {str(e)}')
    
    context = {'page_title': 'Import Teachers'}
    return render(request, 'teachers/teacher_import.html', context)


@login_required
@user_passes_test(is_admin)
def teacher_export(request):
    """Export teachers to CSV"""
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="teachers.csv"'
    
    writer = csv.writer(response)
    writer.writerow([
        'teacher_id', 'employee_id', 'first_name', 'last_name', 'middle_name', 
        'email', 'phone', 'gender', 'date_of_birth', 'designation', 
        'department', 'employment_type', 'date_of_joining', 'status'
    ])
    
    teachers = Teacher.objects.select_related('department').all()
    for teacher in teachers:
        writer.writerow([
            teacher.teacher_id,
            teacher.employee_id,
            teacher.first_name,
            teacher.last_name,
            teacher.middle_name,
            teacher.email,
            teacher.phone,
            teacher.gender,
            teacher.date_of_birth,
            teacher.designation,
            str(teacher.department) if teacher.department else '',
            teacher.employment_type,
            teacher.date_of_joining,
            teacher.status,
        ])
    
    return response
