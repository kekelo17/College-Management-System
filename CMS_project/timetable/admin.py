from django.contrib import admin
from .models import (
    Building, Room, TimeSlot, Timetable, TimetableEntry,
    TeacherAvailability, RoomBooking, Substitution
)


@admin.register(Building)
class BuildingAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'floors', 'location', 'total_rooms', 'is_active']
    list_filter = ['is_active']
    search_fields = ['code', 'name', 'location']


@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    list_display = ['room_number', 'name', 'building', 'room_type', 'capacity', 
                   'has_projector', 'has_ac', 'is_active']
    list_filter = ['room_type', 'building', 'is_active', 'has_projector', 'has_ac']
    search_fields = ['room_number', 'name', 'building__name']
    readonly_fields = ['created_at', 'updated_at', 'available_capacity']


@admin.register(TimeSlot)
class TimeSlotAdmin(admin.ModelAdmin):
    list_display = ['day', 'start_time', 'end_time', 'duration_minutes', 'slot_order', 'is_break']
    list_filter = ['day', 'is_break', 'is_active']
    search_fields = ['day']
    ordering = ['day', 'slot_order', 'start_time']


@admin.register(Timetable)
class TimetableAdmin(admin.ModelAdmin):
    list_display = ['name', 'semester', 'department', 'level', 'status', 
                   'is_current', 'effective_from']
    list_filter = ['status', 'is_current', 'semester']
    search_fields = ['name', 'department__name']
    readonly_fields = ['created_at', 'updated_at', 'approved_at']


@admin.register(TimetableEntry)
class TimetableEntryAdmin(admin.ModelAdmin):
    list_display = ['timetable', 'course', 'teacher', 'room', 'day', 'time_slot', 'entry_type']
    list_filter = ['day', 'entry_type', 'timetable__status']
    search_fields = ['course__code', 'course__name', 'teacher__first_name', 'teacher__last_name']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(TeacherAvailability)
class TeacherAvailabilityAdmin(admin.ModelAdmin):
    list_display = ['teacher', 'day', 'time_slot', 'is_available']
    list_filter = ['day', 'is_available']
    search_fields = ['teacher__first_name', 'teacher__last_name']


@admin.register(RoomBooking)
class RoomBookingAdmin(admin.ModelAdmin):
    list_display = ['room', 'booked_by', 'title', 'booking_type', 'start_datetime', 
                   'end_datetime', 'status']
    list_filter = ['booking_type', 'status', 'is_recurring']
    search_fields = ['title', 'room__room_number', 'room__building__name', 'booked_by__first_name']
    readonly_fields = ['created_at', 'updated_at', 'duration_hours']


@admin.register(Substitution)
class SubstitutionAdmin(admin.ModelAdmin):
    list_display = ['original_teacher', 'substitute_teacher', 'date', 'time_slot', 'status']
    list_filter = ['status', 'date']
    search_fields = ['original_teacher__first_name', 'original_teacher__last_name',
                    'substitute_teacher__first_name', 'substitute_teacher__last_name']
    readonly_fields = ['created_at', 'updated_at']
