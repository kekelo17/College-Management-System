from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
import uuid


class Teacher(models.Model):
    """Model for teachers/instructors"""
    GENDER_CHOICES = [
        ('M', 'Male'),
        ('F', 'Female'),
        ('O', 'Other'),
    ]
    
    BLOOD_GROUP_CHOICES = [
        ('A+', 'A+'), ('A-', 'A-'),
        ('B+', 'B+'), ('B-', 'B-'),
        ('AB+', 'AB+'), ('AB-', 'AB-'),
        ('O+', 'O+'), ('O-', 'O-'),
    ]
    
    EMPLOYMENT_TYPE_CHOICES = [
        ('full_time', 'Full Time'),
        ('part_time', 'Part Time'),
        ('contract', 'Contract'),
        ('visiting', 'Visiting'),
    ]
    
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('on_leave', 'On Leave'),
        ('terminated', 'Terminated'),
    ]

    teacher_id = models.CharField(max_length=20, unique=True, editable=False)
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True)
    
    # Personal Information
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    middle_name = models.CharField(max_length=100, blank=True)
    date_of_birth = models.DateField()
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES)
    blood_group = models.CharField(max_length=3, choices=BLOOD_GROUP_CHOICES, blank=True)
    
    # Contact Information
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20)
    alternative_phone = models.CharField(max_length=20, blank=True)
    address = models.TextField()
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    country = models.CharField(max_length=100, default='Nigeria')
    postal_code = models.CharField(max_length=20, blank=True)
    
    # Professional Information
    employee_id = models.CharField(max_length=50, unique=True)
    department = models.ForeignKey('courses.Department', on_delete=models.SET_NULL, null=True, blank=True)
    designation = models.CharField(max_length=100)  # Professor, Lecturer, etc.
    employment_type = models.CharField(max_length=20, choices=EMPLOYMENT_TYPE_CHOICES, default='full_time')
    subjects = models.ManyToManyField('courses.Course', blank=True, related_name='teachers')
    
    # Employment Details
    date_of_joining = models.DateField()
    date_of_confirmation = models.DateField(null=True, blank=True)
    salary = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    
    # Additional Information
    passport_photo = models.ImageField(upload_to='teachers/photos/', blank=True, null=True)
    nationality = models.CharField(max_length=100, default='Nigerian')
    state_of_origin = models.CharField(max_length=100, blank=True)
    marital_status = models.CharField(max_length=20, blank=True)
    spouse_name = models.CharField(max_length=200, blank=True)
    emergency_contact = models.CharField(max_length=20, blank=True)
    emergency_contact_name = models.CharField(max_length=200, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.teacher_id} - {self.first_name} {self.last_name}"

    def save(self, *args, **kwargs):
        if not self.teacher_id:
            self.teacher_id = f"T-{str(uuid.uuid4().int)[:6].upper()}"
            while Teacher.objects.filter(teacher_id=self.teacher_id).exists():
                self.teacher_id = f"T-{str(uuid.uuid4().int)[:6].upper()}"
        super().save(*args, **kwargs)

    @property
    def full_name(self):
        return f"{self.first_name} {self.middle_name} {self.last_name}".strip()

    @property
    def total_courses(self):
        return self.subjects.count()

    @property
    def total_students(self):
        from courses.models import CourseEnrollment
        return CourseEnrollment.objects.filter(course__in=self.subjects.all()).values('student').distinct().count()


class TeacherQualification(models.Model):
    """Model for teacher qualifications"""
    QUALIFICATION_TYPE_CHOICES = [
        ('bsc', 'B.Sc'),
        ('msc', 'M.Sc'),
        ('phd', 'Ph.D'),
        ('pgde', 'PGDE'),
        ('nd', 'ND'),
        ('hnd', 'HND'),
        ('nce', 'NCE'),
        ('other', 'Other'),
    ]

    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE, related_name='qualifications')
    qualification_type = models.CharField(max_length=20, choices=QUALIFICATION_TYPE_CHOICES)
    degree = models.CharField(max_length=200)
    institution = models.CharField(max_length=200)
    field_of_study = models.CharField(max_length=200)
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    grade = models.CharField(max_length=50, blank=True)
    is_highest = models.BooleanField(default=False)
    certificate = models.FileField(upload_to='teachers/qualifications/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-end_date']

    def __str__(self):
        return f"{self.teacher} - {self.degree}"


class TeacherExperience(models.Model):
    """Model for teacher work experience"""
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE, related_name='experiences')
    organization = models.CharField(max_length=200)
    position = models.CharField(max_length=200)
    department = models.CharField(max_length=100, blank=True)
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    is_current = models.BooleanField(default=False)
    responsibilities = models.TextField(blank=True)
    salary = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-start_date']
        verbose_name_plural = 'Teacher Experiences'

    def __str__(self):
        return f"{self.teacher} - {self.position} at {self.organization}"


class TeacherDocument(models.Model):
    """Model for teacher documents"""
    DOCUMENT_TYPE_CHOICES = [
        ('cv', 'CV/Resume'),
        ('certificate', 'Professional Certificate'),
        ('license', 'Teaching License'),
        ('id_card', 'ID Card'),
        ('nin', 'NIN'),
        ('passport', 'International Passport'),
        ('other', 'Other'),
    ]

    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE, related_name='documents')
    document_type = models.CharField(max_length=20, choices=DOCUMENT_TYPE_CHOICES)
    title = models.CharField(max_length=200)
    file = models.FileField(upload_to='teachers/documents/')
    issue_date = models.DateField(null=True, blank=True)
    expiry_date = models.DateField(null=True, blank=True)
    is_verified = models.BooleanField(default=False)
    notes = models.TextField(blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = 'Teacher Documents'
        ordering = ['-uploaded_at']

    def __str__(self):
        return f"{self.teacher} - {self.get_document_type_display()}"


class TeacherLeave(models.Model):
    """Model for teacher leave applications"""
    LEAVE_TYPE_CHOICES = [
        ('annual', 'Annual Leave'),
        ('sick', 'Sick Leave'),
        ('maternity', 'Maternity Leave'),
        ('paternity', 'Paternity Leave'),
        ('study', 'Study Leave'),
        ('unpaid', 'Unpaid Leave'),
        ('other', 'Other'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('cancelled', 'Cancelled'),
    ]

    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE, related_name='leaves')
    leave_type = models.CharField(max_length=20, choices=LEAVE_TYPE_CHOICES)
    start_date = models.DateField()
    end_date = models.DateField()
    reason = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_leaves')
    approved_date = models.DateTimeField(null=True, blank=True)
    rejection_reason = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.teacher} - {self.get_leave_type_display()} ({self.start_date} to {self.end_date})"

    @property
    def duration(self):
        return (self.end_date - self.start_date).days + 1
