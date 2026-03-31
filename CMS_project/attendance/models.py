from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator


class Attendance(models.Model):
    """Model for attendance sessions"""
    STATUS_CHOICES = [
        ('scheduled', 'Scheduled'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]

    course = models.ForeignKey('courses.Course', on_delete=models.CASCADE, related_name='attendance_sessions')
    teacher = models.ForeignKey('teachers.Teacher', on_delete=models.CASCADE, related_name='attendance_sessions')
    semester = models.ForeignKey('students.Semester', on_delete=models.CASCADE, related_name='attendance_sessions')
    
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    duration = models.DurationField(null=True, blank=True)
    
    topic = models.CharField(max_length=200, blank=True)
    notes = models.TextField(blank=True)
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='scheduled')
    is_approved = models.BooleanField(default=False)
    approved_by = models.ForeignKey('teachers.Teacher', on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_attendances')
    
    # Settings
    is_mandatory = models.BooleanField(default=True)
    late_threshold = models.DurationField(null=True, blank=True)  # Time after which student is marked late
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-date', '-start_time']

    def __str__(self):
        return f"{self.course} - {self.date} ({self.start_time})"

    @property
    def total_students(self):
        return self.records.count()

    @property
    def present_count(self):
        return self.records.filter(status='present').count()

    @property
    def absent_count(self):
        return self.records.filter(status='absent').count()

    @property
    def late_count(self):
        return self.records.filter(status='late').count()

    @property
    def attendance_percentage(self):
        if self.total_students == 0:
            return 0
        return round((self.present_count / self.total_students) * 100, 1)


class AttendanceRecord(models.Model):
    """Model for individual attendance records"""
    STATUS_CHOICES = [
        ('present', 'Present'),
        ('absent', 'Absent'),
        ('late', 'Late'),
        ('excused', 'Excused'),
    ]

    attendance = models.ForeignKey(Attendance, on_delete=models.CASCADE, related_name='records')
    student = models.ForeignKey('students.Student', on_delete=models.CASCADE, related_name='attendance_records')
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)
    marked_by = models.ForeignKey('teachers.Teacher', on_delete=models.SET_NULL, null=True, related_name='marked_attendances')
    marked_time = models.DateTimeField(auto_now_add=True)
    updated_time = models.DateTimeField(auto_now=True)
    
    # Additional details
    arrival_time = models.TimeField(null=True, blank=True)
    reason = models.TextField(blank=True)
    is_approved = models.BooleanField(default=False)
    approved_by = models.ForeignKey('teachers.Teacher', on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_records')
    
    # Verification
    is_verified = models.BooleanField(default=False)
    verification_method = models.CharField(max_length=50, blank=True)  # manual, biometric, rfid, etc.
    
    notes = models.TextField(blank=True)

    class Meta:
        unique_together = ['attendance', 'student']
        ordering = ['attendance__date', 'student__last_name']

    def __str__(self):
        return f"{self.student} - {self.attendance} - {self.get_status_display()}"

    @property
    def is_present(self):
        return self.status in ['present', 'late']


class AttendanceSummary(models.Model):
    """Model for monthly/weekly attendance summaries"""
    student = models.ForeignKey('students.Student', on_delete=models.CASCADE, related_name='attendance_summaries')
    semester = models.ForeignKey('students.Semester', on_delete=models.CASCADE, related_name='attendance_summaries')
    
    # Period
    start_date = models.DateField()
    end_date = models.DateField()
    period_type = models.CharField(max_length=20)  # weekly, monthly
    
    # Counts
    total_sessions = models.PositiveIntegerField(default=0)
    present_count = models.PositiveIntegerField(default=0)
    absent_count = models.PositiveIntegerField(default=0)
    late_count = models.PositiveIntegerField(default=0)
    excused_count = models.PositiveIntegerField(default=0)
    
    # Percentage
    attendance_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['student', 'semester', 'start_date', 'period_type']
        ordering = ['-start_date']

    def __str__(self):
        return f"{self.student} - {self.period_type} ({self.start_date} to {self.end_date})"


class AttendanceLeave(models.Model):
    """Model for attendance leave/excused absences"""
    LEAVE_TYPE_CHOICES = [
        ('sick', 'Sick Leave'),
        ('emergency', 'Emergency'),
        ('academic', 'Academic Activity'),
        ('religious', 'Religious Activity'),
        ('other', 'Other'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]

    student = models.ForeignKey('students.Student', on_delete=models.CASCADE, related_name='attendance_leaves')
    leave_type = models.CharField(max_length=20, choices=LEAVE_TYPE_CHOICES)
    
    start_date = models.DateField()
    end_date = models.DateField()
    reason = models.TextField()
    
    attachment = models.FileField(upload_to='attendance/leaves/', blank=True, null=True)
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    approved_by = models.ForeignKey('teachers.Teacher', on_delete=models.SET_NULL, null=True, blank=True)
    approved_date = models.DateTimeField(null=True, blank=True)
    rejection_reason = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.student} - {self.get_leave_type_display()} ({self.start_date} to {self.end_date})"

    @property
    def duration(self):
        return (self.end_date - self.start_date).days + 1
