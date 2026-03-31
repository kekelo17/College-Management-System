from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.db.models import Q
from django.core.paginator import Paginator

from .models import Department, Course, CourseEnrollment, Subject, Prerequisite
from teachers.models import Teacher
from students.models import Student, Semester
from core.views import log_activity


def is_admin(user):
    return user.is_superuser or user.is_staff


def is_teacher_or_admin(user):
    return user.is_superuser or user.is_staff or hasattr(user, 'teacher')


# Department Views
@login_required
@user_passes_test(is_admin)
def department_list(request):
    """List all departments"""
    departments = Department.objects.select_related('head', 'faculty').all()
    context = {
        'page_title': 'Departments',
        'departments': departments,
    }
    return render(request, 'courses/department_list.html', context)


@login_required
@user_passes_test(is_admin)
def department_create(request):
    """Create a new department"""
    if request.method == 'POST':
        try:
            department = Department(
                code=request.POST.get('code'),
                name=request.POST.get('name'),
                faculty_id=request.POST.get('faculty') or None,
                head_id=request.POST.get('head') or None,
                description=request.POST.get('description', ''),
                mission=request.POST.get('mission', ''),
                vision=request.POST.get('vision', ''),
                established_date=request.POST.get('established_date') or None,
            )
            department.save()
            messages.success(request, f'Department {department.name} created successfully!')
            return redirect('courses:department_detail', pk=department.pk)
        except Exception as e:
            messages.error(request, f'Error creating department: {str(e)}')
    
    departments = Department.objects.filter(is_active=True)
    teachers = Teacher.objects.filter(status='active')
    context = {
        'page_title': 'Add Department',
        'departments': departments,
        'teachers': teachers,
    }
    return render(request, 'courses/department_form.html', context)


@login_required
@user_passes_test(is_admin)
def department_detail(request, pk):
    """View department details"""
    department = get_object_or_404(Department, pk=pk)
    courses = Course.objects.filter(department=department)
    teachers = Teacher.objects.filter(department=department)
    
    context = {
        'page_title': f'{department.name} - Department Details',
        'department': department,
        'courses': courses,
        'teachers': teachers,
    }
    return render(request, 'courses/department_detail.html', context)


@login_required
@user_passes_test(is_admin)
def department_update(request, pk):
    """Update a department"""
    department = get_object_or_404(Department, pk=pk)
    
    if request.method == 'POST':
        try:
            department.code = request.POST.get('code')
            department.name = request.POST.get('name')
            department.faculty_id = request.POST.get('faculty') or None
            department.head_id = request.POST.get('head') or None
            department.description = request.POST.get('description', '')
            department.mission = request.POST.get('mission', '')
            department.vision = request.POST.get('vision', '')
            department.established_date = request.POST.get('established_date') or None
            department.is_active = 'is_active' in request.POST
            department.save()
            
            messages.success(request, f'Department {department.name} updated successfully!')
            return redirect('courses:department_detail', pk=department.pk)
        except Exception as e:
            messages.error(request, f'Error updating department: {str(e)}')
    
    departments = Department.objects.filter(is_active=True)
    teachers = Teacher.objects.filter(status='active')
    context = {
        'page_title': f'Edit {department.name}',
        'department': department,
        'departments': departments,
        'teachers': teachers,
    }
    return render(request, 'courses/department_form.html', context)


@login_required
@user_passes_test(is_admin)
def department_delete(request, pk):
    """Delete a department"""
    department = get_object_or_404(Department, pk=pk)
    
    if request.method == 'POST':
        department_name = department.name
        department.delete()
        log_activity(request.user, 'delete', 'courses', 'Department', pk, department_name, request=request)
        messages.success(request, f'Department {department_name} deleted successfully!')
        return redirect('courses:department_list')
    
    context = {
        'page_title': 'Delete Department',
        'department': department,
    }
    return render(request, 'courses/department_confirm_delete.html', context)


# Course Views
@login_required
@user_passes_test(is_admin)
def course_list(request):
    """List all courses"""
    query = request.GET.get('q', '')
    department = request.GET.get('department', '')
    level = request.GET.get('level', '')
    
    courses = Course.objects.select_related('department', 'teacher').all()
    
    if query:
        courses = courses.filter(
            Q(code__icontains=query) |
            Q(name__icontains=query)
        )
    
    if department:
        courses = courses.filter(department_id=department)
    
    if level:
        courses = courses.filter(level=level)
    
    departments = Department.objects.filter(is_active=True)
    enrollments = CourseEnrollment.objects.select_related('student', 'course', 'semester').all()[:50]  # Recent enrollments
    
    paginator = Paginator(courses, 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_title': 'Courses',
        'courses': page_obj,
        'departments': departments,
        'enrollments': enrollments,
        'query': query,
        'selected_department': department,
        'selected_level': level,
    }
    return render(request, 'courses/course_list.html', context)


@login_required
@user_passes_test(is_admin)
def course_create(request):
    """Create a new course"""
    if request.method == 'POST':
        try:
            course = Course(
                code=request.POST.get('code'),
                name=request.POST.get('name'),
                department_id=request.POST.get('department'),
                teacher_id=request.POST.get('teacher') or None,
                description=request.POST.get('description', ''),
                syllabus=request.POST.get('syllabus', ''),
                objectives=request.POST.get('objectives', ''),
                credit_units=request.POST.get('credit_units', 3),
                level=request.POST.get('level'),
                semester=request.POST.get('semester'),
                course_type=request.POST.get('course_type', 'core'),
                max_capacity=request.POST.get('max_capacity', 100),
                min_capacity=request.POST.get('min_capacity', 10),
                lecture_hours=request.POST.get('lecture_hours', 3),
                practical_hours=request.POST.get('practical_hours', 0),
                tutorial_hours=request.POST.get('tutorial_hours', 0),
                continuous_assessment_weight=request.POST.get('ca_weight', 40),
                exam_weight=request.POST.get('exam_weight', 60),
                pass_mark=request.POST.get('pass_mark', 40),
                course_fee=request.POST.get('course_fee', 0),
            )
            course.save()
            
            log_activity(request.user, 'create', 'courses', 'Course', course.id, str(course), request=request)
            messages.success(request, f'Course {course.name} created successfully!')
            return redirect('courses:course_detail', pk=course.pk)
        except Exception as e:
            messages.error(request, f'Error creating course: {str(e)}')
    
    departments = Department.objects.filter(is_active=True)
    teachers = Teacher.objects.filter(status='active')
    context = {
        'page_title': 'Add Course',
        'departments': departments,
        'teachers': teachers,
    }
    return render(request, 'courses/course_form.html', context)


@login_required
@user_passes_test(is_admin)
def course_detail(request, pk):
    """View course details"""
    course = get_object_or_404(Course, pk=pk)
    enrollments = CourseEnrollment.objects.filter(course=course).select_related('student', 'semester')
    prerequisites = course.prerequisites_set.all()
    subjects = course.subjects.all()
    
    context = {
        'page_title': f'{course.code} - {course.name}',
        'course': course,
        'enrollments': enrollments,
        'prerequisites': prerequisites,
        'subjects': subjects,
    }
    return render(request, 'courses/course_detail.html', context)


@login_required
@user_passes_test(is_admin)
def course_update(request, pk):
    """Update a course"""
    course = get_object_or_404(Course, pk=pk)
    
    if request.method == 'POST':
        try:
            course.code = request.POST.get('code')
            course.name = request.POST.get('name')
            course.department_id = request.POST.get('department')
            course.teacher_id = request.POST.get('teacher') or None
            course.description = request.POST.get('description', '')
            course.syllabus = request.POST.get('syllabus', '')
            course.objectives = request.POST.get('objectives', '')
            course.credit_units = request.POST.get('credit_units', 3)
            course.level = request.POST.get('level')
            course.semester = request.POST.get('semester')
            course.course_type = request.POST.get('course_type', 'core')
            course.max_capacity = request.POST.get('max_capacity', 100)
            course.min_capacity = request.POST.get('min_capacity', 10)
            course.lecture_hours = request.POST.get('lecture_hours', 3)
            course.practical_hours = request.POST.get('practical_hours', 0)
            course.tutorial_hours = request.POST.get('tutorial_hours', 0)
            course.continuous_assessment_weight = request.POST.get('ca_weight', 40)
            course.exam_weight = request.POST.get('exam_weight', 60)
            course.pass_mark = request.POST.get('pass_mark', 40)
            course.course_fee = request.POST.get('course_fee', 0)
            course.status = request.POST.get('status', 'active')
            course.save()
            
            log_activity(request.user, 'update', 'courses', 'Course', course.id, str(course), request=request)
            messages.success(request, f'Course {course.name} updated successfully!')
            return redirect('courses:course_detail', pk=course.pk)
        except Exception as e:
            messages.error(request, f'Error updating course: {str(e)}')
    
    departments = Department.objects.filter(is_active=True)
    teachers = Teacher.objects.filter(status='active')
    context = {
        'page_title': f'Edit {course.name}',
        'course': course,
        'departments': departments,
        'teachers': teachers,
    }
    return render(request, 'courses/course_form.html', context)


@login_required
@user_passes_test(is_admin)
def course_delete(request, pk):
    """Delete a course"""
    course = get_object_or_404(Course, pk=pk)
    
    if request.method == 'POST':
        course_name = course.name
        course.delete()
        log_activity(request.user, 'delete', 'courses', 'Course', pk, course_name, request=request)
        messages.success(request, f'Course {course_name} deleted successfully!')
        return redirect('courses:course_list')
    
    context = {
        'page_title': 'Delete Course',
        'course': course,
    }
    return render(request, 'courses/course_confirm_delete.html', context)


# Enrollment Views
@login_required
@user_passes_test(is_admin)
def enrollment_list(request):
    """List all enrollments"""
    query = request.GET.get('q', '')
    status = request.GET.get('status', '')
    
    enrollments = CourseEnrollment.objects.select_related('student', 'course', 'semester').all()
    
    if query:
        enrollments = enrollments.filter(
            Q(student__first_name__icontains=query) |
            Q(student__last_name__icontains=query) |
            Q(course__code__icontains=query) |
            Q(course__name__icontains=query)
        )
    
    if status:
        enrollments = enrollments.filter(status=status)
    
    paginator = Paginator(enrollments, 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_title': 'Course Enrollments',
        'page_obj': page_obj,
        'query': query,
        'selected_status': status,
    }
    return render(request, 'courses/enrollment_list.html', context)


@login_required
@user_passes_test(is_admin)
def enrollment_create(request):
    """Create a new enrollment"""
    if request.method == 'POST':
        try:
            enrollment = CourseEnrollment(
                student_id=request.POST.get('student'),
                course_id=request.POST.get('course'),
                semester_id=request.POST.get('semester'),
                status=request.POST.get('status', 'enrolled'),
                is_repeat='is_repeat' in request.POST,
            )
            enrollment.save()
            
            messages.success(request, 'Enrollment created successfully!')
            return redirect('courses:enrollment_list')
        except Exception as e:
            messages.error(request, f'Error creating enrollment: {str(e)}')
    
    students = Student.objects.filter(status='active')
    courses = Course.objects.filter(status='active')
    semesters = Semester.objects.filter(is_active=True)
    
    context = {
        'page_title': 'Create Enrollment',
        'students': students,
        'courses': courses,
        'semesters': semesters,
    }
    return render(request, 'courses/enrollment_form.html', context)


@login_required
@user_passes_test(is_admin)
def enrollment_update(request, pk):
    """Update an enrollment"""
    enrollment = get_object_or_404(CourseEnrollment, pk=pk)
    
    if request.method == 'POST':
        try:
            enrollment.status = request.POST.get('status', 'enrolled')
            enrollment.is_active = 'is_active' in request.POST
            enrollment.ca_score = request.POST.get('ca_score') or None
            enrollment.exam_score = request.POST.get('exam_score') or None
            enrollment.total_score = request.POST.get('total_score') or None
            enrollment.grade = request.POST.get('grade', '')
            enrollment.save()
            
            if enrollment.ca_score is not None and enrollment.exam_score is not None:
                enrollment.calculate_total()
            
            messages.success(request, 'Enrollment updated successfully!')
            return redirect('courses:enrollment_list')
        except Exception as e:
            messages.error(request, f'Error updating enrollment: {str(e)}')
    
    context = {
        'page_title': 'Edit Enrollment',
        'enrollment': enrollment,
    }
    return render(request, 'courses/enrollment_form.html', context)


@login_required
@user_passes_test(is_admin)
def enrollment_delete(request, pk):
    """Delete an enrollment"""
    enrollment = get_object_or_404(CourseEnrollment, pk=pk)
    
    if request.method == 'POST':
        enrollment.delete()
        messages.success(request, 'Enrollment deleted successfully!')
        return redirect('courses:enrollment_list')
    
    context = {
        'page_title': 'Delete Enrollment',
        'enrollment': enrollment,
    }
    return render(request, 'courses/enrollment_confirm_delete.html', context)


# Subject Views
@login_required
@user_passes_test(is_admin)
def subject_create(request, course_pk):
    """Add a subject to a course"""
    course = get_object_or_404(Course, pk=course_pk)
    
    if request.method == 'POST':
        try:
            subject = Subject(
                course=course,
                name=request.POST.get('name'),
                code=request.POST.get('code'),
                teacher_id=request.POST.get('teacher') or None,
                description=request.POST.get('description', ''),
                learning_outcomes=request.POST.get('learning_outcomes', ''),
                topics=request.POST.get('topics', ''),
                order=request.POST.get('order', 0),
            )
            subject.save()
            
            messages.success(request, f'Subject {subject.name} added successfully!')
            return redirect('courses:course_detail', pk=course_pk)
        except Exception as e:
            messages.error(request, f'Error adding subject: {str(e)}')
    
    teachers = Teacher.objects.filter(status='active')
    context = {
        'page_title': f'Add Subject to {course.name}',
        'course': course,
        'teachers': teachers,
    }
    return render(request, 'courses/subject_form.html', context)


@login_required
@user_passes_test(is_admin)
def subject_update(request, pk):
    """Update a subject"""
    subject = get_object_or_404(Subject, pk=pk)
    course_pk = subject.course.pk
    
    if request.method == 'POST':
        try:
            subject.name = request.POST.get('name')
            subject.code = request.POST.get('code')
            subject.teacher_id = request.POST.get('teacher') or None
            subject.description = request.POST.get('description', '')
            subject.learning_outcomes = request.POST.get('learning_outcomes', '')
            subject.topics = request.POST.get('topics', '')
            subject.order = request.POST.get('order', 0)
            subject.is_active = 'is_active' in request.POST
            subject.save()
            
            messages.success(request, f'Subject {subject.name} updated successfully!')
            return redirect('courses:course_detail', pk=course_pk)
        except Exception as e:
            messages.error(request, f'Error updating subject: {str(e)}')
    
    teachers = Teacher.objects.filter(status='active')
    context = {
        'page_title': f'Edit {subject.name}',
        'subject': subject,
        'teachers': teachers,
    }
    return render(request, 'courses/subject_form.html', context)


@login_required
@user_passes_test(is_admin)
def subject_delete(request, pk):
    """Delete a subject"""
    subject = get_object_or_404(Subject, pk=pk)
    course_pk = subject.course.pk
    
    if request.method == 'POST':
        subject.delete()
        messages.success(request, 'Subject deleted successfully!')
        return redirect('courses:course_detail', pk=course_pk)
    
    context = {
        'page_title': 'Delete Subject',
        'subject': subject,
    }
    return render(request, 'courses/subject_confirm_delete.html', context)


# Prerequisite Views
@login_required
@user_passes_test(is_admin)
def prerequisite_add(request, course_pk):
    """Add a prerequisite to a course"""
    course = get_object_or_404(Course, pk=course_pk)
    
    if request.method == 'POST':
        try:
            prerequisite = Prerequisite(
                course=course,
                prerequisite_id=request.POST.get('prerequisite'),
                is_mandatory='is_mandatory' in request.POST,
            )
            prerequisite.save()
            
            messages.success(request, 'Prerequisite added successfully!')
            return redirect('courses:course_detail', pk=course_pk)
        except Exception as e:
            messages.error(request, f'Error adding prerequisite: {str(e)}')
    
    courses = Course.objects.filter(department=course.department).exclude(pk=course.pk)
    context = {
        'page_title': f'Add Prerequisite to {course.name}',
        'course': course,
        'courses': courses,
    }
    return render(request, 'courses/prerequisite_form.html', context)


@login_required
@user_passes_test(is_admin)
def prerequisite_delete(request, pk):
    """Delete a prerequisite"""
    prerequisite = get_object_or_404(Prerequisite, pk=pk)
    course_pk = prerequisite.course.pk
    
    if request.method == 'POST':
        prerequisite.delete()
        messages.success(request, 'Prerequisite deleted successfully!')
        return redirect('courses:course_detail', pk=course_pk)
    
    context = {
        'page_title': 'Delete Prerequisite',
        'prerequisite': prerequisite,
    }
    return render(request, 'courses/prerequisite_confirm_delete.html', context)
