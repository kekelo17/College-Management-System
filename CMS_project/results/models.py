from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError


class Grade(models.Model):
    """Model for grading system"""
    grade = models.CharField(max_length=2, unique=True)
    min_score = models.PositiveIntegerField()
    max_score = models.PositiveIntegerField()
    grade_point = models.DecimalField(max_digits=3, decimal_places=2)
    description = models.CharField(max_length=100, blank=True)
    is_passing = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['-max_score']
        verbose_name_plural = 'Grades'

    def __str__(self):
        return f"{self.grade} ({self.min_score}-{self.max_score})"

    def clean(self):
        if self.min_score > self.max_score:
            raise ValidationError('Min score cannot be greater than max score')


class Exam(models.Model):
    """Model for exams"""
    EXAM_TYPE_CHOICES = [
        ('midterm', 'Midterm Exam'),
        ('final', 'Final Exam'),
        ('quiz', 'Quiz'),
        ('test', 'Test'),
        ('assignment', 'Assignment'),
        ('practical', 'Practical Exam'),
        ('project', 'Project'),
    ]
    
    STATUS_CHOICES = [
        ('upcoming', 'Upcoming'),
        ('ongoing', 'Ongoing'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
        ('published', 'Published'),
    ]

    course = models.ForeignKey('courses.Course', on_delete=models.CASCADE, related_name='exams')
    semester = models.ForeignKey('students.Semester', on_delete=models.CASCADE, related_name='exams')
    teacher = models.ForeignKey('teachers.Teacher', on_delete=models.CASCADE, related_name='exams')
    
    title = models.CharField(max_length=200)
    exam_type = models.CharField(max_length=20, choices=EXAM_TYPE_CHOICES)
    
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    duration = models.DurationField()  # in minutes
    
    total_marks = models.DecimalField(max_digits=5, decimal_places=2)
    passing_marks = models.DecimalField(max_digits=5, decimal_places=2)
    
    instructions = models.TextField(blank=True)
    venue = models.CharField(max_length=200, blank=True)
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='upcoming')
    is_published = models.BooleanField(default=False)
    published_at = models.DateTimeField(null=True, blank=True)
    
    weight = models.PositiveIntegerField(default=0)  # Weight in overall assessment
    allow_retake = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-date', '-start_time']

    def __str__(self):
        return f"{self.course} - {self.title} ({self.date})"

    @property
    def duration_hours(self):
        return self.duration.total_seconds() / 3600


class Result(models.Model):
    """Model for student results"""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('submitted', 'Submitted'),
        ('reviewed', 'Reviewed'),
        ('published', 'Published'),
        ('rejected', 'Rejected'),
    ]

    student = models.ForeignKey('students.Student', on_delete=models.CASCADE, related_name='results')
    course = models.ForeignKey('courses.Course', on_delete=models.CASCADE, related_name='results')
    semester = models.ForeignKey('students.Semester', on_delete=models.CASCADE, related_name='results')
    exam = models.ForeignKey(Exam, on_delete=models.SET_NULL, null=True, blank=True, related_name='results')
    
    # Scores
    ca_score = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True,
                                   validators=[MinValueValidator(0), MaxValueValidator(100)])
    exam_score = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True,
                                     validators=[MinValueValidator(0), MaxValueValidator(100)])
    total_score = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    
    # Grade
    grade = models.ForeignKey(Grade, on_delete=models.SET_NULL, null=True, blank=True)
    grade_point = models.DecimalField(max_digits=3, decimal_places=2, null=True, blank=True)
    letter_grade = models.CharField(max_length=2, blank=True)
    
    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    is_passed = models.BooleanField(default=False)
    is_repeat = models.BooleanField(default=False)
    
    # Additional
    rank = models.PositiveIntegerField(null=True, blank=True)
    remarks = models.TextField(blank=True)
    teacher_remarks = models.TextField(blank=True)
    
    # Metadata
    submitted_by = models.ForeignKey('teachers.Teacher', on_delete=models.SET_NULL, null=True, related_name='submitted_results')
    submitted_at = models.DateTimeField(null=True, blank=True)
    published_at = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['student', 'course', 'semester', 'exam']
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.student} - {self.course} - {self.total_score}"

    def calculate_total(self):
        if self.ca_score is not None and self.exam_score is not None:
            self.total_score = self.ca_score + self.exam_score
            self.determine_grade()
            self.save()
        return self.total_score

    def determine_grade(self):
        if self.total_score is not None:
            grade = Grade.objects.filter(
                min_score__lte=self.total_score,
                max_score__gte=self.total_score
            ).first()
            if grade:
                self.grade = grade
                self.grade_point = grade.grade_point
                self.letter_grade = grade.grade
                self.is_passed = grade.is_passing


class ResultBulkUpload(models.Model):
    """Model for bulk result uploads"""
    semester = models.ForeignKey('students.Semester', on_delete=models.CASCADE, related_name='result_uploads')
    course = models.ForeignKey('courses.Course', on_delete=models.CASCADE, related_name='result_uploads')
    uploaded_by = models.ForeignKey('teachers.Teacher', on_delete=models.CASCADE, related_name='result_uploads')
    
    file = models.FileField(upload_to='results/uploads/')
    total_records = models.PositiveIntegerField(default=0)
    successful_records = models.PositiveIntegerField(default=0)
    failed_records = models.PositiveIntegerField(default=0)
    
    error_log = models.TextField(blank=True)
    is_processed = models.BooleanField(default=False)
    processed_at = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Bulk Upload - {self.course} ({self.created_at.date()})"


class SemesterResult(models.Model):
    """Model for semester results summary"""
    student = models.ForeignKey('students.Student', on_delete=models.CASCADE, related_name='semester_results')
    semester = models.ForeignKey('students.Semester', on_delete=models.CASCADE, related_name='results_summary')
    
    # Calculated fields
    total_courses = models.PositiveIntegerField(default=0)
    courses_passed = models.PositiveIntegerField(default=0)
    courses_failed = models.PositiveIntegerField(default=0)
    
    total_credit_units = models.PositiveIntegerField(default=0)
    earned_credit_units = models.PositiveIntegerField(default=0)
    
    total_score = models.DecimalField(max_digits=7, decimal_places=2, default=0)
    gpa = models.DecimalField(max_digits=4, decimal_places=2, default=0)
    cgpa = models.DecimalField(max_digits=4, decimal_places=2, default=0)
    
    # Standing
    class_rank = models.PositiveIntegerField(null=True, blank=True)
    total_students = models.PositiveIntegerField(default=0)
    
    # Status
    is_complete = models.BooleanField(default=False)
    status = models.CharField(max_length=20, default='pending')
    remarks = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['student', 'semester']
        ordering = ['-semester']

    def __str__(self):
        return f"{self.student} - {self.semester} - GPA: {self.gpa}"

    def calculate_gpa(self):
        from courses.models import CourseEnrollment
        enrollments = CourseEnrollment.objects.filter(
            student=self.student,
            semester__academic_year=self.semester.academic_year,
            semester__name=self.semester.name
        )
        
        total_points = 0
        total_credits = 0
        
        for enrollment in enrollments:
            if enrollment.grade and enrollment.course.credit_units:
                total_points += float(enrollment.grade.grade_point) * enrollment.course.credit_units
                total_credits += enrollment.course.credit_units
        
        if total_credits > 0:
            self.gpa = round(total_points / total_credits, 2)
        return self.gpa


class Assessment(models.Model):
    """Model for individual assessments within a course"""
    ASSESSMENT_TYPE_CHOICES = [
        ('test', 'Test'),
        ('quiz', 'Quiz'),
        ('assignment', 'Assignment'),
        ('project', 'Project'),
        ('practical', 'Practical'),
        ('midterm', 'Midterm'),
    ]

    course = models.ForeignKey('courses.Course', on_delete=models.CASCADE, related_name='assessments')
    semester = models.ForeignKey('students.Semester', on_delete=models.CASCADE, related_name='assessments')
    teacher = models.ForeignKey('teachers.Teacher', on_delete=models.CASCADE, related_name='assessments')
    
    title = models.CharField(max_length=200)
    assessment_type = models.CharField(max_length=20, choices=ASSESSMENT_TYPE_CHOICES)
    
    date = models.DateField()
    due_date = models.DateTimeField(null=True, blank=True)
    
    total_marks = models.DecimalField(max_digits=5, decimal_places=2)
    weight = models.PositiveIntegerField(default=0)  # Percentage weight in CA
    
    instructions = models.TextField(blank=True)
    is_published = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-date']

    def __str__(self):
        return f"{self.course} - {self.title}"


class AssessmentScore(models.Model):
    """Model for individual assessment scores"""
    assessment = models.ForeignKey(Assessment, on_delete=models.CASCADE, related_name='scores')
    student = models.ForeignKey('students.Student', on_delete=models.CASCADE, related_name='assessment_scores')
    
    score = models.DecimalField(max_digits=5, decimal_places=2)
    is_submitted = models.BooleanField(default=False)
    submitted_at = models.DateTimeField(null=True, blank=True)
    
    remarks = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['assessment', 'student']
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.student} - {self.assessment}: {self.score}"
