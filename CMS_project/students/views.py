from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.db.models import Q, Count
from django.core.paginator import Paginator
from django.core.files.storage import default_storage
from django.utils import timezone
from datetime import datetime
import csv
import io

from .models import Student, Guardian, StudentDocument, StudentClass, AcademicYear, Semester
from courses.models import Department
from fees.models import Invoice, Payment
from attendance.models import AttendanceRecord
from results.models import Result, SemesterResult
from core.views import log_activity


def is_admin(user):
    return user.is_superuser or user.is_staff


@login_required
@user_passes_test(is_admin)
def student_list(request):
    """List all students with filtering and pagination"""
    query = request.GET.get('q', '')
    department = request.GET.get('department', '')
    status = request.GET.get('status', '')
    
    students = Student.objects.select_related('department', 'current_semester').all()
    
    if query:
        students = students.filter(
            Q(student_id__icontains=query) |
            Q(first_name__icontains=query) |
            Q(last_name__icontains=query) |
            Q(email__icontains=query) |
            Q(phone__icontains=query)
        )
    
    if department:
        students = students.filter(department_id=department)
    
    if status:
        students = students.filter(status=status)
    
    departments = Department.objects.filter(is_active=True)
    
    paginator = Paginator(students, 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_title': 'Students',
        'students': page_obj,
        'departments': departments,
        'query': query,
        'selected_department': department,
        'selected_status': status,
        'classes': [],  # Add if you have Class model
    }
    return render(request, 'students/student_list.html', context)


@login_required
@user_passes_test(is_admin)
def student_create(request):
    """Create a new student"""
    if request.method == 'POST':
        try:
            # Parse dates safely
            dob_str = request.POST.get('date_of_birth')
            if not dob_str:
                raise ValueError('Date of birth is required')
            date_of_birth = datetime.strptime(dob_str, '%Y-%m-%d').date()

            adm_str = request.POST.get('admission_date')
            admission_date = (
                datetime.strptime(adm_str, '%Y-%m-%d').date()
                if adm_str
                else timezone.now().date()
            )

            # Normalize optional text fields to avoid None/NULL issues
            def val(name, default=''):
                return request.POST.get(name, default) or default

            student = Student(
                first_name=val('first_name'),
                last_name=val('last_name'),
                middle_name=val('middle_name'),
                date_of_birth=date_of_birth,
                gender=val('gender'),
                blood_group=val('blood_group'),
                email=val('email'),
                phone=val('phone'),
                address=val('address'),
                city=val('city'),
                state=val('state'),
                country=val('country', 'Nigeria'),
                postal_code=val('postal_code'),
                admission_date=admission_date,
                department_id=request.POST.get('department') or None,
                current_semester_id=request.POST.get('current_semester') or None,
                nationality=val('nationality', 'Nigerian'),
                religion=val('religion'),
                state_of_origin=val('state_of_origin'),
                local_govt=val('local_govt'),
                status='active' if request.POST.get('is_active', 'True') == 'True' else 'inactive',
            )
            student.save()
            
            # Handle user creation
            username = request.POST.get('username')
            password1 = request.POST.get('password1')
            password2 = request.POST.get('password2')
            if username and password1:
                if password1 != password2:
                    raise ValueError('Passwords do not match')
                from django.contrib.auth.models import User
                user = User.objects.create_user(
                    username=username,
                    email=student.email,
                    password=password1,
                    first_name=student.first_name,
                    last_name=student.last_name,
                    is_active=request.POST.get('is_active', 'True') == 'True'
                )
                student.user = user
                student.save()
            
            # Handle passport photo upload
            if request.FILES.get('passport_photo') or request.FILES.get('profile_picture'):
                student.passport_photo = request.FILES.get('passport_photo') or request.FILES.get('profile_picture')
                student.save()

            # Optional guardian creation
            if request.POST.get('guardian_name') and request.POST.get('guardian_relation'):
                Guardian.objects.create(
                    student=student,
                    name=request.POST.get('guardian_name'),
                    relationship=request.POST.get('guardian_relation').lower(),
                    email=request.POST.get('guardian_email', ''),
                    phone=request.POST.get('guardian_phone', ''),
                    occupation=request.POST.get('guardian_occupation', '')
                )
            
            log_activity(request.user, 'create', 'students', 'Student', student.id, str(student), request=request)
            messages.success(request, f'Student {student.full_name} created successfully!')
            return redirect('students:student_detail', pk=student.pk)
        except Exception as e:
            messages.error(request, f'Error creating student: {str(e)}')
    
    departments = Department.objects.filter(is_active=True)
    semesters = Semester.objects.filter(is_active=True)
    academic_years = AcademicYear.objects.all()
    blood_groups = [choice[0] for choice in Student.BLOOD_GROUP_CHOICES]
    
    context = {
        'page_title': 'Add Student',
        'departments': departments,
        'semesters': semesters,
        'academic_years': academic_years,
        'blood_groups': blood_groups,
        'classes': [],
        'form': None,  # template expects this key
    }
    return render(request, 'students/student_form.html', context)


@login_required
@user_passes_test(is_admin)
def student_detail(request, pk):
    """View student details"""
    student = get_object_or_404(Student, pk=pk)
    
    # Guardian
    guardians = student.guardians.all()
    
    # Documents
    documents = student.documents.all()
    
    # Class assignments
    class_assignments = student.class_assignments.select_related('semester').all()
    
    # Attendance
    attendance_records = AttendanceRecord.objects.filter(student=student)[:10]
    total_classes = AttendanceRecord.objects.filter(student=student).count()
    present_classes = AttendanceRecord.objects.filter(student=student, status__in=['present', 'late']).count()
    attendance_percentage = round((present_classes / total_classes * 100), 1) if total_classes > 0 else 0
    
    # Results
    results = Result.objects.filter(student=student).select_related('course', 'exam')[:10]
    
    # Fee Status
    invoices = Invoice.objects.filter(student=student)
    total_payable = sum(inv.total_amount for inv in invoices)
    total_paid = sum(inv.amount_paid for inv in invoices)
    balance = total_payable - total_paid
    
    context = {
        'page_title': f'{student.full_name} - Student Details',
        'student': student,
        'guardians': guardians,
        'documents': documents,
        'class_assignments': class_assignments,
        'attendance_records': attendance_records,
        'total_classes': total_classes,
        'present_classes': present_classes,
        'attendance_percentage': attendance_percentage,
        'results': results,
        'total_payable': total_payable,
        'total_paid': total_paid,
        'balance': balance,
        'invoices': invoices[:5],
    }
    return render(request, 'students/student_detail.html', context)


@login_required
@user_passes_test(is_admin)
def student_update(request, pk):
    """Update student details"""
    student = get_object_or_404(Student, pk=pk)
    
    if request.method == 'POST':
        try:
            def val(name, default=''):
                return request.POST.get(name, default) or default

            dob_str = request.POST.get('date_of_birth')
            if dob_str:
                student.date_of_birth = datetime.strptime(dob_str, '%Y-%m-%d').date()

            adm_str = request.POST.get('admission_date')
            if adm_str:
                student.admission_date = datetime.strptime(adm_str, '%Y-%m-%d').date()

            student.first_name = val('first_name')
            student.last_name = val('last_name')
            student.middle_name = val('middle_name')
            student.gender = val('gender')
            student.blood_group = val('blood_group')
            student.email = val('email')
            student.phone = val('phone')
            student.address = val('address')
            student.city = val('city')
            student.state = val('state')
            student.country = val('country', 'Nigeria')
            student.postal_code = val('postal_code')
            student.department_id = request.POST.get('department') or None
            student.current_semester_id = request.POST.get('current_semester') or None
            student.nationality = val('nationality', 'Nigerian')
            student.religion = val('religion')
            student.state_of_origin = val('state_of_origin')
            student.local_govt = val('local_govt')
            is_active = request.POST.get('is_active', 'True') == 'True'
            student.status = 'active' if is_active else 'inactive'
            
            if request.FILES.get('passport_photo') or request.FILES.get('profile_picture'):
                student.passport_photo = request.FILES.get('passport_photo') or request.FILES.get('profile_picture')
            
            student.save()

            if student.user:
                student.user.is_active = is_active
                student.user.first_name = student.first_name
                student.user.last_name = student.last_name
                student.user.email = student.email
                student.user.save()
            
            log_activity(request.user, 'update', 'students', 'Student', student.id, str(student), request=request)
            messages.success(request, f'Student {student.full_name} updated successfully!')
            return redirect('students:student_detail', pk=student.pk)
        except Exception as e:
            messages.error(request, f'Error updating student: {str(e)}')
    
    departments = Department.objects.filter(is_active=True)
    semesters = Semester.objects.filter(is_active=True)
    academic_years = AcademicYear.objects.all()
    blood_groups = [choice[0] for choice in Student.BLOOD_GROUP_CHOICES]
    
    context = {
        'page_title': f'Edit {student.full_name}',
        'student': student,
        'departments': departments,
        'semesters': semesters,
        'academic_years': academic_years,
        'blood_groups': blood_groups,
        'classes': [],
        'form': None,
    }
    return render(request, 'students/student_form.html', context)


@login_required
@user_passes_test(is_admin)
def student_delete(request, pk):
    """Delete a student"""
    student = get_object_or_404(Student, pk=pk)
    
    if request.method == 'POST':
        student_name = student.full_name
        student.delete()
        log_activity(request.user, 'delete', 'students', 'Student', pk, student_name, request=request)
        messages.success(request, f'Student {student_name} deleted successfully!')
        return redirect('students:student_list')
    
    context = {
        'page_title': 'Delete Student',
        'student': student,
    }
    return render(request, 'students/student_confirm_delete.html', context)


@login_required
def student_profile(request):
    """Student's own profile view"""
    if not hasattr(request.user, 'student'):
        messages.error(request, 'You are not registered as a student.')
        return redirect('dashboard')
    
    student = request.user.student
    return student_detail(request, student.pk)


# Academic Year Views
@login_required
@user_passes_test(is_admin)
def academic_year_list(request):
    """List all academic years"""
    academic_years = AcademicYear.objects.all()
    context = {
        'page_title': 'Academic Years',
        'academic_years': academic_years,
    }
    return render(request, 'students/academic_year_list.html', context)


@login_required
@user_passes_test(is_admin)
def academic_year_create(request):
    """Create a new academic year"""
    if request.method == 'POST':
        try:
            academic_year = AcademicYear(
                name=request.POST.get('name'),
                start_date=request.POST.get('start_date'),
                end_date=request.POST.get('end_date'),
                is_current='is_current' in request.POST,
            )
            academic_year.save()
            
            # Create semesters for this academic year
            first_sem_start = request.POST.get('first_sem_start')
            first_sem_end = request.POST.get('first_sem_end')
            second_sem_start = request.POST.get('second_sem_start')
            second_sem_end = request.POST.get('second_sem_end')
            
            if first_sem_start and first_sem_end:
                Semester.objects.create(
                    academic_year=academic_year,
                    name='1',
                    start_date=first_sem_start,
                    end_date=first_sem_end,
                    is_active=True
                )
            
            if second_sem_start and second_sem_end:
                Semester.objects.create(
                    academic_year=academic_year,
                    name='2',
                    start_date=second_sem_start,
                    end_date=second_sem_end,
                    is_active=False
                )
            
            messages.success(request, f'Academic Year {academic_year.name} created successfully!')
            return redirect('students:academic_year_list')
        except Exception as e:
            messages.error(request, f'Error creating academic year: {str(e)}')
    
    context = {'page_title': 'Add Academic Year'}
    return render(request, 'students/academic_year_form.html', context)


@login_required
@user_passes_test(is_admin)
def academic_year_update(request, pk):
    """Update an academic year"""
    academic_year = get_object_or_404(AcademicYear, pk=pk)
    
    if request.method == 'POST':
        try:
            academic_year.name = request.POST.get('name')
            academic_year.start_date = request.POST.get('start_date')
            academic_year.end_date = request.POST.get('end_date')
            academic_year.is_current = 'is_current' in request.POST
            academic_year.save()
            
            messages.success(request, f'Academic Year {academic_year.name} updated successfully!')
            return redirect('students:academic_year_list')
        except Exception as e:
            messages.error(request, f'Error updating academic year: {str(e)}')
    
    context = {
        'page_title': f'Edit {academic_year.name}',
        'academic_year': academic_year,
    }
    return render(request, 'students/academic_year_form.html', context)


# Semester Views
@login_required
@user_passes_test(is_admin)
def semester_list(request):
    """List all semesters"""
    semesters = Semester.objects.select_related('academic_year').all()
    context = {
        'page_title': 'Semesters',
        'semesters': semesters,
    }
    return render(request, 'students/semester_list.html', context)


@login_required
@user_passes_test(is_admin)
def semester_create(request):
    """Create a new semester"""
    if request.method == 'POST':
        try:
            semester = Semester(
                academic_year_id=request.POST.get('academic_year'),
                name=request.POST.get('name'),
                start_date=request.POST.get('start_date'),
                end_date=request.POST.get('end_date'),
                is_active='is_active' in request.POST,
            )
            semester.save()
            
            messages.success(request, f'Semester {semester} created successfully!')
            return redirect('students:semester_list')
        except Exception as e:
            messages.error(request, f'Error creating semester: {str(e)}')
    
    academic_years = AcademicYear.objects.all()
    context = {
        'page_title': 'Add Semester',
        'academic_years': academic_years,
    }
    return render(request, 'students/semester_form.html', context)


@login_required
@user_passes_test(is_admin)
def semester_update(request, pk):
    """Update a semester"""
    semester = get_object_or_404(Semester, pk=pk)
    
    if request.method == 'POST':
        try:
            semester.academic_year_id = request.POST.get('academic_year')
            semester.name = request.POST.get('name')
            semester.start_date = request.POST.get('start_date')
            semester.end_date = request.POST.get('end_date')
            semester.is_active = 'is_active' in request.POST
            semester.save()
            
            messages.success(request, f'Semester {semester} updated successfully!')
            return redirect('students:semester_list')
        except Exception as e:
            messages.error(request, f'Error updating semester: {str(e)}')
    
    academic_years = AcademicYear.objects.all()
    context = {
        'page_title': f'Edit {semester}',
        'semester': semester,
        'academic_years': academic_years,
    }
    return render(request, 'students/semester_form.html', context)


# Guardian Views
@login_required
@user_passes_test(is_admin)
def guardian_create(request, student_pk):
    """Add a guardian to a student"""
    student = get_object_or_404(Student, pk=student_pk)
    
    if request.method == 'POST':
        try:
            guardian = Guardian(
                student=student,
                name=request.POST.get('name'),
                relationship=request.POST.get('relationship'),
                email=request.POST.get('email', ''),
                phone=request.POST.get('phone'),
                alternative_phone=request.POST.get('alternative_phone', ''),
                occupation=request.POST.get('occupation', ''),
                workplace=request.POST.get('workplace', ''),
                address=request.POST.get('address', ''),
                is_primary='is_primary' in request.POST,
            )
            guardian.save()
            
            messages.success(request, f'Guardian {guardian.name} added successfully!')
            return redirect('students:student_detail', pk=student_pk)
        except Exception as e:
            messages.error(request, f'Error adding guardian: {str(e)}')
    
    context = {
        'page_title': f'Add Guardian for {student.full_name}',
        'student': student,
    }
    return render(request, 'students/guardian_form.html', context)


@login_required
@user_passes_test(is_admin)
def guardian_update(request, pk):
    """Update a guardian"""
    guardian = get_object_or_404(Guardian, pk=pk)
    student = guardian.student
    
    if request.method == 'POST':
        try:
            guardian.name = request.POST.get('name')
            guardian.relationship = request.POST.get('relationship')
            guardian.email = request.POST.get('email', '')
            guardian.phone = request.POST.get('phone')
            guardian.alternative_phone = request.POST.get('alternative_phone', '')
            guardian.occupation = request.POST.get('occupation', '')
            guardian.workplace = request.POST.get('workplace', '')
            guardian.address = request.POST.get('address', '')
            guardian.is_primary = 'is_primary' in request.POST
            guardian.save()
            
            messages.success(request, f'Guardian {guardian.name} updated successfully!')
            return redirect('students:student_detail', pk=student.pk)
        except Exception as e:
            messages.error(request, f'Error updating guardian: {str(e)}')
    
    context = {
        'page_title': f'Edit Guardian {guardian.name}',
        'guardian': guardian,
        'student': student,
    }
    return render(request, 'students/guardian_form.html', context)


# Document Views
@login_required
@user_passes_test(is_admin)
def document_create(request, student_pk):
    """Add a document to a student"""
    student = get_object_or_404(Student, pk=student_pk)
    
    if request.method == 'POST':
        try:
            document = StudentDocument(
                student=student,
                document_type=request.POST.get('document_type'),
                title=request.POST.get('title'),
                file=request.FILES.get('file'),
                issue_date=request.POST.get('issue_date') or None,
                expiry_date=request.POST.get('expiry_date') or None,
                notes=request.POST.get('notes', ''),
            )
            document.save()
            
            messages.success(request, f'Document {document.title} uploaded successfully!')
            return redirect('students:student_detail', pk=student_pk)
        except Exception as e:
            messages.error(request, f'Error uploading document: {str(e)}')
    
    context = {
        'page_title': f'Upload Document for {student.full_name}',
        'student': student,
    }
    return render(request, 'students/document_form.html', context)


@login_required
@user_passes_test(is_admin)
def document_delete(request, pk):
    """Delete a student document"""
    document = get_object_or_404(StudentDocument, pk=pk)
    student_pk = document.student.pk
    
    if request.method == 'POST':
        document.delete()
        messages.success(request, 'Document deleted successfully!')
        return redirect('students:student_detail', pk=student_pk)
    
    context = {
        'page_title': 'Delete Document',
        'document': document,
    }
    return render(request, 'students/document_confirm_delete.html', context)


# Class Assignment Views
@login_required
@user_passes_test(is_admin)
def student_class_add(request, student_pk):
    """Add a class assignment to a student"""
    student = get_object_or_404(Student, pk=student_pk)
    
    if request.method == 'POST':
        try:
            assignment = StudentClass(
                student=student,
                semester_id=request.POST.get('semester'),
                level=request.POST.get('level'),
                section=request.POST.get('section', ''),
                roll_number=request.POST.get('roll_number', ''),
                is_active=True,
            )
            assignment.save()
            
            messages.success(request, f'Class assignment added for {student.full_name}!')
            return redirect('students:student_detail', pk=student_pk)
        except Exception as e:
            messages.error(request, f'Error adding class assignment: {str(e)}')
    
    semesters = Semester.objects.filter(is_active=True)
    context = {
        'page_title': f'Add Class for {student.full_name}',
        'student': student,
        'semesters': semesters,
    }
    return render(request, 'students/student_class_form.html', context)


# Bulk Operations
@login_required
@user_passes_test(is_admin)
def student_import(request):
    """Import students from CSV"""
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
                    student = Student(
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
                        admission_date=row.get('admission_date'),
                        nationality=row.get('nationality', 'Nigerian'),
                        status='active',
                    )
                    student.save()
                    imported_count += 1
                except Exception as e:
                    error_count += 1
                    errors.append(f"Row error: {str(e)}")
            
            messages.success(request, f'Successfully imported {imported_count} students. {error_count} errors.')
            if errors:
                for error in errors[:10]:
                    messages.warning(request, error)
            
            return redirect('students:student_list')
        except Exception as e:
            messages.error(request, f'Error importing students: {str(e)}')
    
    context = {'page_title': 'Import Students'}
    return render(request, 'students/student_import.html', context)


@login_required
@user_passes_test(is_admin)
def student_export(request):
    """Export students to CSV"""
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="students.csv"'
    
    writer = csv.writer(response)
    writer.writerow([
        'student_id', 'first_name', 'last_name', 'middle_name', 'email', 'phone',
        'gender', 'date_of_birth', 'address', 'city', 'state', 'country',
        'admission_date', 'status', 'department', 'current_semester'
    ])
    
    students = Student.objects.select_related('department', 'current_semester').all()
    for student in students:
        writer.writerow([
            student.student_id,
            student.first_name,
            student.last_name,
            student.middle_name,
            student.email,
            student.phone,
            student.gender,
            student.date_of_birth,
            student.address,
            student.city,
            student.state,
            student.country,
            student.admission_date,
            student.status,
            str(student.department) if student.department else '',
            str(student.current_semester) if student.current_semester else '',
        ])
    
    return response
