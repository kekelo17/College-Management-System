from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator


class Building(models.Model):
    """Model for buildings"""
    code = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=200)
    floors = models.PositiveIntegerField(default=1)
    location = models.CharField(max_length=200, blank=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return f"{self.code} - {self.name}"

    @property
    def total_rooms(self):
        return self.rooms.count()


class Room(models.Model):
    """Model for rooms/classrooms"""
    ROOM_TYPE_CHOICES = [
        ('classroom', 'Classroom'),
        ('laboratory', 'Laboratory'),
        ('lecture_hall', 'Lecture Hall'),
        ('workshop', 'Workshop'),
        ('seminar_room', 'Seminar Room'),
        ('auditorium', 'Auditorium'),
        ('staff_room', 'Staff Room'),
        ('office', 'Office'),
        ('library', 'Library'),
    ]

    room_number = models.CharField(max_length=20)
    name = models.CharField(max_length=100, blank=True)
    building = models.ForeignKey(Building, on_delete=models.CASCADE, related_name='rooms')
    floor = models.PositiveIntegerField(default=1)
    
    room_type = models.CharField(max_length=20, choices=ROOM_TYPE_CHOICES)
    capacity = models.PositiveIntegerField(default=40)
    current_capacity = models.PositiveIntegerField(default=0)
    
    # Facilities
    has_projector = models.BooleanField(default=False)
    has_ac = models.BooleanField(default=False)
    has_whiteboard = models.BooleanField(default=False)
    has_computer = models.BooleanField(default=False)
    has_internet = models.BooleanField(default=False)
    
    is_active = models.BooleanField(default=True)
    description = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['building', 'room_number']
        ordering = ['building', 'room_number']

    def __str__(self):
        return f"{self.building.code}-{self.room_number}"

    @property
    def available_capacity(self):
        return self.capacity - self.current_capacity


class TimeSlot(models.Model):
    """Model for time slots in a day"""
    DAY_CHOICES = [
        ('monday', 'Monday'),
        ('tuesday', 'Tuesday'),
        ('wednesday', 'Wednesday'),
        ('thursday', 'Thursday'),
        ('friday', 'Friday'),
        ('saturday', 'Saturday'),
        ('sunday', 'Sunday'),
    ]

    day = models.CharField(max_length=10, choices=DAY_CHOICES)
    start_time = models.TimeField()
    end_time = models.TimeField()
    slot_order = models.PositiveIntegerField(default=0)
    
    duration_minutes = models.PositiveIntegerField(default=60)
    is_break = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['day', 'start_time', 'end_time']
        ordering = ['day', 'slot_order', 'start_time']

    def __str__(self):
        return f"{self.get_day_display()} - {self.start_time} to {self.end_time}"

    def save(self, *args, **kwargs):
        if self.start_time and self.end_time:
            from datetime import datetime, timedelta
            start = datetime.combine(datetime.today(), self.start_time)
            end = datetime.combine(datetime.today(), self.end_time)
            self.duration_minutes = int((end - start).total_seconds() / 60)
        super().save(*args, **kwargs)


class Timetable(models.Model):
    """Model for master timetable"""
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('published', 'Published'),
        ('archived', 'Archived'),
    ]

    name = models.CharField(max_length=200)
    semester = models.ForeignKey('students.Semester', on_delete=models.CASCADE, related_name='timetables')
    department = models.ForeignKey('courses.Department', on_delete=models.CASCADE, null=True, blank=True, related_name='timetables')
    level = models.CharField(max_length=10, blank=True)
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    is_current = models.BooleanField(default=False)
    
    effective_from = models.DateField()
    effective_to = models.DateField(null=True, blank=True)
    
    approved_by = models.ForeignKey('teachers.Teacher', on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_timetables')
    approved_at = models.DateTimeField(null=True, blank=True)
    
    notes = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['semester', 'department', 'level']
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} ({self.semester})"

    def save(self, *args, **kwargs):
        if self.is_current:
            Timetable.objects.filter(is_current=True).update(is_current=False)
        super().save(*args, **kwargs)


class TimetableEntry(models.Model):
    """Model for individual timetable entries"""
    ENTRY_TYPE_CHOICES = [
        ('lecture', 'Lecture'),
        ('practical', 'Practical'),
        ('tutorial', 'Tutorial'),
        ('break', 'Break'),
        ('assembly', 'Assembly'),
        ('exam', 'Exam'),
    ]

    timetable = models.ForeignKey(Timetable, on_delete=models.CASCADE, related_name='entries')
    course = models.ForeignKey('courses.Course', on_delete=models.CASCADE, related_name='timetable_entries')
    teacher = models.ForeignKey('teachers.Teacher', on_delete=models.SET_NULL, null=True, blank=True, related_name='timetable_entries')
    room = models.ForeignKey(Room, on_delete=models.SET_NULL, null=True, blank=True, related_name='timetable_entries')
    
    time_slot = models.ForeignKey(TimeSlot, on_delete=models.CASCADE, related_name='entries')
    day = models.CharField(max_length=10, choices=TimeSlot.DAY_CHOICES)
    
    entry_type = models.CharField(max_length=20, choices=ENTRY_TYPE_CHOICES, default='lecture')
    
    # For recurring entries
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    weeks = models.CharField(max_length=100, blank=True)  # e.g., "1,2,3,4,5,6,7,8,9,10,11,12,13,14"
    
    is_active = models.BooleanField(default=True)
    notes = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['timetable', 'time_slot', 'day', 'course']
        ordering = ['timetable', 'day', 'time_slot__slot_order']

    def __str__(self):
        return f"{self.course} - {self.get_day_display()} - {self.time_slot}"


class TeacherAvailability(models.Model):
    """Model for teacher availability"""
    teacher = models.ForeignKey('teachers.Teacher', on_delete=models.CASCADE, related_name='availability')
    
    day = models.CharField(max_length=10, choices=TimeSlot.DAY_CHOICES)
    time_slot = models.ForeignKey(TimeSlot, on_delete=models.CASCADE, related_name='teacher_availability')
    
    is_available = models.BooleanField(default=True)
    reason = models.TextField(blank=True)  # If not available
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['teacher', 'day', 'time_slot']
        ordering = ['teacher', 'day', 'time_slot__slot_order']

    def __str__(self):
        return f"{self.teacher} - {self.get_day_display()} - {self.time_slot}"


class RoomBooking(models.Model):
    """Model for room bookings"""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('cancelled', 'Cancelled'),
    ]
    
    BOOKING_TYPE_CHOICES = [
        ('class', 'Class'),
        ('exam', 'Exam'),
        ('meeting', 'Meeting'),
        ('event', 'Event'),
        ('other', 'Other'),
    ]

    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name='bookings')
    booked_by = models.ForeignKey('teachers.Teacher', on_delete=models.CASCADE, related_name='room_bookings')
    
    title = models.CharField(max_length=200)
    booking_type = models.CharField(max_length=20, choices=BOOKING_TYPE_CHOICES)
    
    start_datetime = models.DateTimeField()
    end_datetime = models.DateTimeField()
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    is_recurring = models.BooleanField(default=False)
    recurrence_pattern = models.CharField(max_length=100, blank=True)  # e.g., "weekly", "daily"
    recurrence_end_date = models.DateField(null=True, blank=True)
    
    attendees = models.PositiveIntegerField(default=0)
    purpose = models.TextField(blank=True)
    
    approved_by = models.ForeignKey('teachers.Teacher', on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_bookings')
    approved_at = models.DateTimeField(null=True, blank=True)
    
    notes = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-start_datetime']

    def __str__(self):
        return f"{self.room} - {self.title} ({self.start_datetime})"

    @property
    def duration_hours(self):
        return (self.end_datetime - self.start_datetime).total_seconds() / 3600


class Substitution(models.Model):
    """Model for teacher substitutions"""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
        ('completed', 'Completed'),
    ]

    original_teacher = models.ForeignKey('teachers.Teacher', on_delete=models.CASCADE, related_name='substitutions_given')
    substitute_teacher = models.ForeignKey('teachers.Teacher', on_delete=models.CASCADE, related_name='substitutions_taken')
    
    timetable_entry = models.ForeignKey(TimetableEntry, on_delete=models.CASCADE, related_name='substitutions')
    
    date = models.DateField()
    time_slot = models.ForeignKey(TimeSlot, on_delete=models.CASCADE, related_name='substitutions')
    
    reason = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    approved_by = models.ForeignKey('teachers.Teacher', on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_substitutions')
    approved_at = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-date', '-created_at']

    def __str__(self):
        return f"{self.original_teacher} -> {self.substitute_teacher} on {self.date}"
