from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.db.models import Q, Avg, Count
from django.core.paginator import Paginator
from django.utils import timezone
from datetime import datetime, timedelta

from .models import Grade, Exam, Result, SemesterResult, Assessment, AssessmentScore, ResultBulkUpload
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


# Grade Views
@login_required
@user_passes_test(is_admin)
def grade_list(request):
    """List all grades"""
    grades = Grade.objects.all().order_by('-max_score')
    context = {
        'page_title': 'Grading System',
        'grades': grades,
    }
    return render(request, 'results/grade_list.html', context)


@login_required
@user_passes_test(is_admin)
def grade_create(request):
    """Create a new grade"""
    if request.method == 'POST':
        try:
            grade = Grade(
                grade=request.POST.get('grade'),
                min_score=request.POST.get('min_score'),
                max_score=request.POST.get('max_score'),
                grade_point=request.POST.get('grade_point'),
                description=request.POST.get('description', ''),
                is_passing='is_passing' in request.POST,
            )
            grade.save()
            
            messages.success(request, f'Grade {grade.grade} created successfully!')
            return redirect('results:grade_list')
        except Exception as e:
            messages.error(request, f'Error creating grade: {str(e)}')
    
    context = {'page_title': 'Add Grade'}
    return render(request, 'results/grade_form.html', context)


@login_required
@user_passes_test(is_admin)
def grade_update(request, pk):
    """Update a grade"""
    grade = get_object_or_404(Grade, pk=pk)
    
    if request.method == 'POST':
        try:
            grade.grade = request.POST.get('grade')
            grade.min_score = request.POST.get('min_score')
            grade.max_score = request.POST.get('max_score')
            grade.grade_point = request.POST.get('grade_point')
            grade.description = request.POST.get('description', '')
            grade.is_passing = 'is_passing' in request.POST
            grade.save()
            
            messages.success(request, f'Grade {grade.grade} updated successfully!')
            return redirect('results:grade_list')
        except Exception as e:
            messages.error(request, f'Error updating grade: {str(e)}')
    
    context = {
        'page_title': f'Edit Grade {grade.grade}',
        'grade': grade,
    }
    return render(request, 'results/grade_form.html', context)


# Exam Views
@login_required
@user_passes_test(is_teacher_or_admin)
def exam_list(request):
    """List all exams"""
    user = request.user
    
    if user.is_superuser or user.is_staff:
        exams = Exam.objects.select_related('course', 'teacher', 'semester').all()
    else:
        exams = Exam.objects.filter(teacher=user.teacher).select_related('course', 'semester')
    
    course = request.GET.get('course', '')
    status = request.GET.get('status', '')
    
    if course:
        exams = exams.filter(course_id=course)
    if status:
        exams = exams.filter(status=status)
    
    courses = Course.objects.filter(status='active')
    
    context = {
        'page_title': 'Results & Grades',
        'exams': exams,
        'results': Result.objects.select_related('student', 'exam', 'subject').all()[:50],
        'grades': Grade.objects.all()[:20],
        'assessments': Assessment.objects.select_related('subject').all()[:20],
        'courses': courses,
        'selected_course': course,
        'selected_status': status,
    }
    return render(request, 'results/result_list.html', context)


@login_required
@user_passes_test(is_teacher_or_admin)
def exam_create(request):
    """Create a new exam"""
    if request.method == 'POST':
        try:
            exam = Exam(
                course_id=request.POST.get('course'),
                semester_id=request.POST.get('semester'),
                teacher_id=request.POST.get('teacher') or (request.user.teacher.id if hasattr(request.user, 'teacher') else None),
                title=request.POST.get('title'),
                exam_type=request.POST.get('exam_type'),
                date=request.POST.get('date'),
                start_time=request.POST.get('start_time'),
                end_time=request.POST.get('end_time'),
                duration=request.POST.get('duration'),
                total_marks=request.POST.get('total_marks'),
                passing_marks=request.POST.get('passing_marks'),
                instructions=request.POST.get('instructions', ''),
                venue=request.POST.get('venue', ''),
                weight=request.POST.get('weight', 0),
                allow_retake='allow_retake' in request.POST,
            )
            exam.save()
            
            messages.success(request, f'Exam {exam.title} created successfully!')
            return redirect('results:exam_detail', pk=exam.pk)
        except Exception as e:
            messages.error(request, f'Error creating exam: {str(e)}')
    
    if hasattr(request.user, 'teacher'):
        courses = Course.objects.filter(teacher=request.user.teacher, status='active')
    else:
        courses = Course.objects.filter(status='active')
    
    semesters = Semester.objects.filter(is_active=True)
    teachers = Teacher.objects.filter(status='active')
    
    context = {
        'page_title': 'Create Exam',
        'courses': courses,
        'semesters': semesters,
        'teachers': teachers,
    }
    return render(request, 'results/exam_form.html', context)


@login_required
@user_passes_test(is_teacher_or_admin)
def exam_detail(request, pk):
    """View exam details"""
    exam = get_object_or_404(Exam, pk=pk)
    results = exam.results.select_related('student').all()
    
    context = {
        'page_title': f'{exam.title} - Exam Details',
        'exam': exam,
        'results': results,
    }
    return render(request, 'results/exam_detail.html', context)


@login_required
@user_passes_test(is_teacher_or_admin)
def exam_update(request, pk):
    """Update an exam"""
    exam = get_object_or_404(Exam, pk=pk)
    
    if request.method == 'POST':
        try:
            exam.title = request.POST.get('title')
            exam.exam_type = request.POST.get('exam_type')
            exam.date = request.POST.get('date')
            exam.start_time = request.POST.get('start_time')
            exam.end_time = request.POST.get('end_time')
            exam.duration = request.POST.get('duration')
            exam.total_marks = request.POST.get('total_marks')
            exam.passing_marks = request.POST.get('passing_marks')
            exam.instructions = request.POST.get('instructions', '')
            exam.venue = request.POST.get('venue', '')
            exam.status = request.POST.get('status', 'upcoming')
            exam.weight = request.POST.get('weight', 0)
            exam.allow_retake = 'allow_retake' in request.POST
            exam.save()
            
            messages.success(request, f'Exam {exam.title} updated successfully!')
            return redirect('results:exam_detail', pk=pk)
        except Exception as e:
            messages.error(request, f'Error updating exam: {str(e)}')
    
    context = {
        'page_title': f'Edit {exam.title}',
        'exam': exam,
    }
    return render(request, 'results/exam_form.html', context)


@login_required
@user_passes_test(is_admin)
def exam_delete(request, pk):
    """Delete an exam"""
    exam = get_object_or_404(Exam, pk=pk)
    
    if request.method == 'POST':
        exam.delete()
        messages.success(request, 'Exam deleted successfully!')
        return redirect('results:exam_list')
    
    context = {
        'page_title': 'Delete Exam',
        'exam': exam,
    }
    return render(request, 'results/exam_confirm_delete.html', context)


# Result Views
@login_required
@user_passes_test(is_teacher_or_admin)
def result_list(request):
    """List all results"""
    user = request.user
    
    if user.is_superuser or user.is_staff:
        results = Result.objects.select_related('student', 'course', 'exam', 'semester').all()
    else:
        results = Result.objects.filter(course__teacher=user.teacher).select_related('student', 'course', 'exam', 'semester')
    
    course = request.GET.get('course', '')
    semester = request.GET.get('semester', '')
    status = request.GET.get('status', '')
    
    if course:
        results = results.filter(course_id=course)
    if semester:
        results = results.filter(semester_id=semester)
    if status:
        results = results.filter(status=status)
    
    courses = Course.objects.filter(status='active')
    semesters = Semester.objects.filter(is_active=True)
    
    context = {
        'page_title': 'Results',
        'results': results[:50],
        'courses': courses,
        'semesters': semesters,
        'selected_course': course,
        'selected_semester': semester,
        'selected_status': status,
    }
    return render(request, 'results/result_list.html', context)


@login_required
@user_passes_test(is_teacher_or_admin)
def result_create(request):
    """Create a new result"""
    if request.method == 'POST':
        try:
            result = Result(
                student_id=request.POST.get('student'),
                course_id=request.POST.get('course'),
                semester_id=request.POST.get('semester'),
                exam_id=request.POST.get('exam') or None,
                ca_score=request.POST.get('ca_score') or None,
                exam_score=request.POST.get('exam_score') or None,
                submitted_by=request.user.teacher if hasattr(request.user, 'teacher') else None,
            )
            
            if result.ca_score is not None and result.exam_score is not None:
                result.calculate_total()
            
            result.save()
            
            messages.success(request, 'Result created successfully!')
            return redirect('results:result_detail', pk=result.pk)
        except Exception as e:
            messages.error(request, f'Error creating result: {str(e)}')
    
    courses = Course.objects.filter(status='active')
    semesters = Semester.objects.filter(is_active=True)
    
    context = {
        'page_title': 'Enter Result',
        'courses': courses,
        'semesters': semesters,
    }
    return render(request, 'results/result_form.html', context)


@login_required
@user_passes_test(is_teacher_or_admin)
def result_detail(request, pk):
    """View result details"""
    result = get_object_or_404(Result, pk=pk)
    
    context = {
        'page_title': f'Result - {result.student} ({result.course})',
        'result': result,
    }
    return render(request, 'results/result_detail.html', context)


@login_required
@user_passes_test(is_teacher_or_admin)
def result_update(request, pk):
    """Update a result"""
    result = get_object_or_404(Result, pk=pk)
    
    if request.method == 'POST':
        try:
            result.ca_score = request.POST.get('ca_score') or None
            result.exam_score = request.POST.get('exam_score') or None
            result.status = request.POST.get('status', 'pending')
            result.remarks = request.POST.get('remarks', '')
            result.teacher_remarks = request.POST.get('teacher_remarks', '')
            
            if result.ca_score is not None and result.exam_score is not None:
                result.calculate_total()
            
            result.save()
            
            messages.success(request, 'Result updated successfully!')
            return redirect('results:result_detail', pk=pk)
        except Exception as e:
            messages.error(request, f'Error updating result: {str(e)}')
    
    context = {
        'page_title': 'Edit Result',
        'result': result,
    }
    return render(request, 'results/result_form.html', context)


@login_required
@user_passes_test(is_teacher_or_admin)
def bulk_result_entry(request):
    """Bulk result entry for a course"""
    if request.method == 'POST':
        course_id = request.POST.get('course')
        semester_id = request.POST.get('semester')
        
        student_ids = request.POST.getlist('student')
        ca_scores = request.POST.getlist('ca_score')
        exam_scores = request.POST.getlist('exam_score')
        
        try:
            for i, student_id in enumerate(student_ids):
                ca = float(ca_scores[i]) if ca_scores[i] else None
                exam = float(exam_scores[i]) if exam_scores[i] else None
                
                if ca is not None or exam is not None:
                    result, created = Result.objects.update_or_create(
                        student_id=student_id,
                        course_id=course_id,
                        semester_id=semester_id,
                        defaults={
                            'ca_score': ca,
                            'exam_score': exam,
                            'submitted_by': request.user.teacher if hasattr(request.user, 'teacher') else None,
                        }
                    )
                    if ca is not None and exam is not None:
                        result.calculate_total()
            
            messages.success(request, 'Results saved successfully!')
            return redirect('results:result_list')
        except Exception as e:
            messages.error(request, f'Error saving results: {str(e)}')
    
    course = request.GET.get('course')
    semester = request.GET.get('semester')
    
    students = []
    if course and semester:
        enrollments = CourseEnrollment.objects.filter(
            course_id=course,
            semester_id=semester
        ).select_related('student')
        students = [e.student for e in enrollments]
    
    courses = Course.objects.filter(status='active')
    semesters = Semester.objects.filter(is_active=True)
    
    context = {
        'page_title': 'Bulk Result Entry',
        'courses': courses,
        'semesters': semesters,
        'students': students,
        'selected_course': course,
        'selected_semester': semester,
    }
    return render(request, 'results/bulk_result_entry.html', context)


@login_required
@user_passes_test(is_teacher_or_admin)
def bulk_result_upload(request):
    """Upload results from file"""
    if request.method == 'POST' and request.FILES.get('file'):
        try:
            # Handle file upload processing
            messages.success(request, 'Results uploaded successfully!')
            return redirect('results:result_list')
        except Exception as e:
            messages.error(request, f'Error uploading results: {str(e)}')
    
    context = {'page_title': 'Upload Results'}
    return render(request, 'results/bulk_result_upload.html', context)


# Semester Result Views
@login_required
@user_passes_test(is_teacher_or_admin)
def semester_result_list(request):
    """List semester results"""
    results = SemesterResult.objects.select_related('student', 'semester').all()
    
    semester = request.GET.get('semester', '')
    if semester:
        results = results.filter(semester_id=semester)
    
    semesters = Semester.objects.filter(is_active=True)
    
    context = {
        'page_title': 'Semester Results',
        'results': results,
        'semesters': semesters,
        'selected_semester': semester,
    }
    return render(request, 'results/semester_result_list.html', context)


@login_required
@user_passes_test(is_teacher_or_admin)
def semester_result_detail(request, pk):
    """View semester result details"""
    result = get_object_or_404(SemesterResult, pk=pk)
    course_results = Result.objects.filter(
        student=result.student,
        semester=result.semester
    ).select_related('course')
    
    context = {
        'page_title': f'Semester Result - {result.student}',
        'result': result,
        'course_results': course_results,
    }
    return render(request, 'results/semester_result_detail.html', context)


@login_required
@user_passes_test(is_teacher_or_admin)
def generate_semester_result(request, pk):
    """Generate semester result for a student"""
    semester = get_object_or_404(Semester, pk=pk)
    student_id = request.GET.get('student')
    
    if student_id:
        student = get_object_or_404(Student, pk=student_id)
        
        try:
            course_results = Result.objects.filter(
                student=student,
                semester=semester,
                status='published'
            )
            
            total_courses = course_results.count()
            courses_passed = course_results.filter(is_passed=True).count()
            courses_failed = total_courses - courses_passed
            
            total_credits = sum(r.course.credit_units for r in course_results if r.course)
            earned_credits = sum(r.course.credit_units for r in course_results.filter(is_passed=True) if r.course)
            
            total_score = sum(float(r.total_score or 0) for r in course_results)
            gpa = round(total_score / total_courses, 2) if total_courses > 0 else 0
            
            sem_result, created = SemesterResult.objects.update_or_create(
                student=student,
                semester=semester,
                defaults={
                    'total_courses': total_courses,
                    'courses_passed': courses_passed,
                    'courses_failed': courses_failed,
                    'total_credit_units': total_credits,
                    'earned_credit_units': earned_credits,
                    'total_score': total_score,
                    'gpa': gpa,
                    'is_complete': True,
                    'status': 'completed',
                }
            )
            
            messages.success(request, f'Semester result generated for {student.full_name}!')
            return redirect('results:semester_result_detail', pk=sem_result.pk)
        except Exception as e:
            messages.error(request, f'Error generating result: {str(e)}')
    
    students = Student.objects.filter(status='active')
    context = {
        'page_title': f'Generate Result for {semester}',
        'semester': semester,
        'students': students,
    }
    return render(request, 'results/generate_semester_result.html', context)


# Assessment Views
@login_required
@user_passes_test(is_teacher_or_admin)
def assessment_list(request):
    """List all assessments"""
    assessments = Assessment.objects.select_related('course', 'semester', 'teacher').all()
    
    context = {
        'page_title': 'Assessments',
        'assessments': assessments,
    }
    return render(request, 'results/assessment_list.html', context)


@login_required
@user_passes_test(is_teacher_or_admin)
def assessment_create(request):
    """Create a new assessment"""
    if request.method == 'POST':
        try:
            assessment = Assessment(
                course_id=request.POST.get('course'),
                semester_id=request.POST.get('semester'),
                teacher_id=request.POST.get('teacher') or (request.user.teacher.id if hasattr(request.user, 'teacher') else None),
                title=request.POST.get('title'),
                assessment_type=request.POST.get('assessment_type'),
                date=request.POST.get('date'),
                total_marks=request.POST.get('total_marks'),
                weight=request.POST.get('weight', 0),
                instructions=request.POST.get('instructions', ''),
            )
            assessment.save()
            
            messages.success(request, f'Assessment {assessment.title} created successfully!')
            return redirect('results:assessment_detail', pk=assessment.pk)
        except Exception as e:
            messages.error(request, f'Error creating assessment: {str(e)}')
    
    courses = Course.objects.filter(status='active')
    semesters = Semester.objects.filter(is_active=True)
    
    context = {
        'page_title': 'Create Assessment',
        'courses': courses,
        'semesters': semesters,
    }
    return render(request, 'results/assessment_form.html', context)


@login_required
@user_passes_test(is_teacher_or_admin)
def assessment_detail(request, pk):
    """View assessment details"""
    assessment = get_object_or_404(Assessment, pk=pk)
    scores = assessment.scores.select_related('student').all()
    
    context = {
        'page_title': f'{assessment.title} - Assessment',
        'assessment': assessment,
        'scores': scores,
    }
    return render(request, 'results/assessment_detail.html', context)


@login_required
@user_passes_test(is_teacher_or_admin)
def assessment_score_entry(request, pk):
    """Enter scores for an assessment"""
    assessment = get_object_or_404(Assessment, pk=pk)
    
    if request.method == 'POST':
        try:
            student_ids = request.POST.getlist('student')
            scores_list = request.POST.getlist('score')
            
            for i, student_id in enumerate(student_ids):
                score_val = scores_list[i] if i < len(scores_list) else None
                if score_val:
                    AssessmentScore.objects.update_or_create(
                        assessment=assessment,
                        student_id=student_id,
                        defaults={'score': score_val}
                    )
            
            messages.success(request, 'Scores saved successfully!')
            return redirect('results:assessment_detail', pk=pk)
        except Exception as e:
            messages.error(request, f'Error saving scores: {str(e)}')
    
    # Get enrolled students
    students = Student.objects.filter(
        course_enrollments__course=assessment.course,
        course_enrollments__semester=assessment.semester,
        course_enrollments__is_active=True
    ).distinct()
    
    context = {
        'page_title': f'Enter Scores - {assessment.title}',
        'assessment': assessment,
        'students': students,
    }
    return render(request, 'results/assessment_score_entry.html', context)


# Student Result Views
@login_required
@user_passes_test(is_student)
def student_results(request):
    """View student's own results"""
    student = request.user.student
    results = Result.objects.filter(student=student, status='published').select_related('course', 'semester')
    
    context = {
        'page_title': 'My Results',
        'results': results,
    }
    return render(request, 'results/student_results.html', context)


@login_required
@user_passes_test(is_student)
def student_transcript(request):
    """View student's transcript"""
    student = request.user.student
    semester_results = SemesterResult.objects.filter(student=student).select_related('semester').order_by('semester__academic_year', 'semester__name')
    
    context = {
        'page_title': 'My Transcript',
        'student': student,
        'semester_results': semester_results,
    }
    return render(request, 'results/student_transcript.html', context)
