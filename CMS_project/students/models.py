from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
import uuid


class AcademicYear(models.Model):
    """Model for academic years"""
    name = models.CharField(max_length=50, unique=True)
    start_date = models.DateField()
    end_date = models.DateField()
    is_current = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-start_date']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if self.is_current:
            AcademicYear.objects.filter(is_current=True).update(is_current=False)
        super().save(*args, **kwargs)


class Semester(models.Model):
    """Model for semesters within academic years"""
    SEMESTER_CHOICES = [
        ('1', 'First Semester'),
        ('2', 'Second Semester'),
        ('3', 'Third Semester'),
    ]
    academic_year = models.ForeignKey(AcademicYear, on_delete=models.CASCADE, related_name='semesters')
    name = models.CharField(max_length=20, choices=SEMESTER_CHOICES)
    start_date = models.DateField()
    end_date = models.DateField()
    is_active = models.BooleanField(default=False)

    class Meta:
        unique_together = ['academic_year', 'name']
        ordering = ['academic_year', 'name']

    def __str__(self):
        return f"{self.academic_year.name} - {self.get_name_display()}"


class Student(models.Model):
    """Model for students"""
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
    
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('suspended', 'Suspended'),
        ('graduated', 'Graduated'),
        ('transferred', 'Transferred'),
    ]

    student_id = models.CharField(max_length=20, unique=True, editable=False)
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
    address = models.TextField()
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    country = models.CharField(max_length=100, default='Nigeria')
    postal_code = models.CharField(max_length=20, blank=True)
    
    # Academic Information
    admission_date = models.DateField()
    current_semester = models.ForeignKey(Semester, on_delete=models.SET_NULL, null=True, blank=True)
    department = models.ForeignKey('courses.Department', on_delete=models.SET_NULL, null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    
    # Additional Information
    passport_photo = models.ImageField(upload_to='students/photos/', blank=True, null=True)
    nationality = models.CharField(max_length=100, default='Nigerian')
    religion = models.CharField(max_length=50, blank=True)
    state_of_origin = models.CharField(max_length=100, blank=True)
    local_govt = models.CharField(max_length=100, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name_plural = 'Students'

    def __str__(self):
        return f"{self.student_id} - {self.first_name} {self.last_name}"

    def save(self, *args, **kwargs):
        if not self.student_id:
            self.student_id = str(uuid.uuid4().int)[:8].upper()
            while Student.objects.filter(student_id=self.student_id).exists():
                self.student_id = str(uuid.uuid4().int)[:8].upper()
        super().save(*args, **kwargs)

    @property
    def full_name(self):
        return f"{self.first_name} {self.middle_name} {self.last_name}".strip()

    @property
    def attendance_rate(self):
        from attendance.models import AttendanceRecord
        records = AttendanceRecord.objects.filter(student=self)
        if not records.exists():
            return 0
        total = records.count()
        present = records.filter(status='present').count()
        return round((present / total) * 100, 1) if total > 0 else 0

    @property
    def gpa(self):
        from results.models import Result
        results = Result.objects.filter(student=self)
        if not results.exists():
            return 0.0
        valid_results = [r for r in results if r.grade_point]
        if not valid_results:
            return 0.0
        total_points = sum(r.grade_point for r in valid_results)
        return round(total_points / len(valid_results), 2)


class Guardian(models.Model):
    """Model for student guardians/parents"""
    RELATIONSHIP_CHOICES = [
        ('father', 'Father'),
        ('mother', 'Mother'),
        ('guardian', 'Guardian'),
        ('sibling', 'Sibling'),
        ('other', 'Other'),
    ]

    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='guardians')
    name = models.CharField(max_length=200)
    relationship = models.CharField(max_length=20, choices=RELATIONSHIP_CHOICES)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=20)
    alternative_phone = models.CharField(max_length=20, blank=True)
    occupation = models.CharField(max_length=100, blank=True)
    workplace = models.CharField(max_length=200, blank=True)
    address = models.TextField(blank=True)
    is_primary = models.BooleanField(default=False)

    class Meta:
        verbose_name_plural = 'Guardians'

    def __str__(self):
        return f"{self.name} ({self.get_relationship_display()}) - {self.student}"


class StudentDocument(models.Model):
    """Model for student documents"""
    DOCUMENT_TYPE_CHOICES = [
        ('birth_cert', 'Birth Certificate'),
        (' WAEC', 'WAEC Result'),
        ('NECO', 'NECO Result'),
        ('JAMB', 'JAMB Result'),
        ('transcript', 'Transcript'),
        ('medical', 'Medical Certificate'),
        ('id_card', 'ID Card'),
        ('passport', 'Passport'),
        ('other', 'Other'),
    ]

    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='documents')
    document_type = models.CharField(max_length=20, choices=DOCUMENT_TYPE_CHOICES)
    title = models.CharField(max_length=200)
    file = models.FileField(upload_to='students/documents/')
    issue_date = models.DateField(null=True, blank=True)
    expiry_date = models.DateField(null=True, blank=True)
    is_verified = models.BooleanField(default=False)
    notes = models.TextField(blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = 'Student Documents'
        ordering = ['-uploaded_at']

    def __str__(self):
        return f"{self.student} - {self.get_document_type_display()}"


class StudentClass(models.Model):
    """Model for student class/level assignments"""
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='class_assignments')
    semester = models.ForeignKey(Semester, on_delete=models.CASCADE)
    level = models.CharField(max_length=10)  # e.g., '100', '200', '300', '400'
    section = models.CharField(max_length=10, blank=True)
    roll_number = models.CharField(max_length=20, blank=True)
    is_active = models.BooleanField(default=True)
    assigned_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['student', 'semester']
        ordering = ['-assigned_at']

    def __str__(self):
        return f"{self.student} - {self.level} ({self.semester})"
