from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator


class Department(models.Model):
    """Model for departments/faculties"""
    code = models.CharField(max_length=10, unique=True)
    name = models.CharField(max_length=200)
    faculty = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='sub_departments')
    head = models.ForeignKey('teachers.Teacher', on_delete=models.SET_NULL, null=True, blank=True, related_name='headed_departments')
    description = models.TextField(blank=True)
    mission = models.TextField(blank=True)
    vision = models.TextField(blank=True)
    established_date = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = 'Departments'
        ordering = ['name']

    def __str__(self):
        return f"{self.code} - {self.name}"

    @property
    def total_courses(self):
        return self.courses.count()

    @property
    def total_students(self):
        return CourseEnrollment.objects.filter(course__department=self).values('student').distinct().count()

    @property
    def total_teachers(self):
        return self.teachers.count()


class Course(models.Model):
    """Model for courses/subjects"""
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('discontinued', 'Discontinued'),
    ]
    
    COURSE_TYPE_CHOICES = [
        ('core', 'Core Course'),
        ('elective', 'Elective Course'),
        ('required', 'Required Course'),
        ('optional', 'Optional Course'),
    ]

    code = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=200)
    department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name='courses')
    teacher = models.ForeignKey('teachers.Teacher', on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_courses')
    
    description = models.TextField(blank=True)
    syllabus = models.TextField(blank=True)
    objectives = models.TextField(blank=True)
    
    # Course Details
    credit_units = models.PositiveIntegerField(default=3)
    level = models.CharField(max_length=10)  # 100, 200, 300, 400, 500
    semester = models.CharField(max_length=10)  # 1, 2, 3
    course_type = models.CharField(max_length=20, choices=COURSE_TYPE_CHOICES, default='core')
    
    # Course Settings
    max_capacity = models.PositiveIntegerField(default=100)
    min_capacity = models.PositiveIntegerField(default=10)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    
    # Contact Hours
    lecture_hours = models.DecimalField(max_digits=4, decimal_places=2, default=3)
    practical_hours = models.DecimalField(max_digits=4, decimal_places=2, default=0)
    tutorial_hours = models.DecimalField(max_digits=4, decimal_places=2, default=0)
    
    # Assessment
    continuous_assessment_weight = models.PositiveIntegerField(
        default=40,
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    exam_weight = models.PositiveIntegerField(
        default=60,
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    pass_mark = models.PositiveIntegerField(default=40)
    
    # Fees
    course_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['department', 'level', 'code']

    def __str__(self):
        return f"{self.code} - {self.name}"

    @property
    def total_hours(self):
        return float(self.lecture_hours) + float(self.practical_hours) + float(self.tutorial_hours)

    @property
    def enrolled_students(self):
        return self.enrollments.filter(is_active=True).count()

    @property
    def average_score(self):
        from results.models import Result
        results = Result.objects.filter(course=self)
        if not results.exists():
            return 0
        return round(sum(r.total_score for r in results) / results.count(), 1)


class CourseEnrollment(models.Model):
    """Model for course enrollments"""
    STATUS_CHOICES = [
        ('enrolled', 'Enrolled'),
        ('pending', 'Pending'),
        ('dropped', 'Dropped'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]

    student = models.ForeignKey('students.Student', on_delete=models.CASCADE, related_name='course_enrollments')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='enrollments')
    semester = models.ForeignKey('students.Semester', on_delete=models.CASCADE, related_name='course_enrollments')
    
    enrollment_date = models.DateField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='enrolled')
    is_active = models.BooleanField(default=True)
    
    # Academic Record
    ca_score = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    exam_score = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    total_score = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    grade = models.CharField(max_length=2, blank=True)
    
    # Additional
    attendance_count = models.PositiveIntegerField(default=0)
    is_repeat = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['student', 'course', 'semester']
        ordering = ['-enrollment_date']

    def __str__(self):
        return f"{self.student} - {self.course} ({self.semester})"

    def calculate_total(self):
        if self.ca_score is not None and self.exam_score is not None:
            self.total_score = self.ca_score + self.exam_score
            self.save()


class Subject(models.Model):
    """Model for subjects within courses"""
    name = models.CharField(max_length=200)
    code = models.CharField(max_length=20, unique=True)
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='subjects')
    teacher = models.ForeignKey('teachers.Teacher', on_delete=models.SET_NULL, null=True, blank=True)
    
    description = models.TextField(blank=True)
    learning_outcomes = models.TextField(blank=True)
    topics = models.TextField(blank=True)
    
    order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['course', 'order', 'name']
        verbose_name_plural = 'Subjects'

    def __str__(self):
        return f"{self.code} - {self.name}"


class Prerequisite(models.Model):
    """Model for course prerequisites"""
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='prerequisites_set')
    prerequisite = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='prerequisites_for')
    is_mandatory = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['course', 'prerequisite']

    def __str__(self):
        return f"{self.course} requires {self.prerequisite}"
