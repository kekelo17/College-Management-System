from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.db.models import Q

from .models import Building, Room, TimeSlot, Timetable, TimetableEntry, RoomBooking, Substitution
from courses.models import Course, Department
from teachers.models import Teacher
from students.models import Semester
from core.views import log_activity


def is_admin(user):
    return user.is_superuser or user.is_staff


def is_teacher_or_admin(user):
    return user.is_superuser or user.is_staff or hasattr(user, 'teacher')


def is_teacher(user):
    return user.is_authenticated and (hasattr(user, 'teacher') or user.is_staff or user.is_superuser)


def is_student(user):
    return user.is_authenticated and hasattr(user, 'student')


# Building Views
@login_required
@user_passes_test(is_admin)
def building_list(request):
    """List all buildings"""
    buildings = Building.objects.all()
    context = {
        'page_title': 'Buildings',
        'buildings': buildings,
    }
    return render(request, 'timetable/building_list.html', context)


@login_required
@user_passes_test(is_admin)
def building_create(request):
    """Create a new building"""
    if request.method == 'POST':
        try:
            building = Building(
                code=request.POST.get('code'),
                name=request.POST.get('name'),
                floors=request.POST.get('floors', 1),
                location=request.POST.get('location', ''),
                description=request.POST.get('description', ''),
            )
            building.save()
            
            messages.success(request, f'Building {building.name} created successfully!')
            return redirect('timetable:building_list')
        except Exception as e:
            messages.error(request, f'Error creating building: {str(e)}')
    
    context = {'page_title': 'Add Building'}
    return render(request, 'timetable/building_form.html', context)


@login_required
@user_passes_test(is_admin)
def building_update(request, pk):
    """Update a building"""
    building = get_object_or_404(Building, pk=pk)
    
    if request.method == 'POST':
        try:
            building.code = request.POST.get('code')
            building.name = request.POST.get('name')
            building.floors = request.POST.get('floors', 1)
            building.location = request.POST.get('location', '')
            building.description = request.POST.get('description', '')
            building.is_active = 'is_active' in request.POST
            building.save()
            
            messages.success(request, f'Building {building.name} updated successfully!')
            return redirect('timetable:building_list')
        except Exception as e:
            messages.error(request, f'Error updating building: {str(e)}')
    
    context = {
        'page_title': f'Edit {building.name}',
        'building': building,
    }
    return render(request, 'timetable/building_form.html', context)


# Room Views
@login_required
@user_passes_test(is_admin)
def room_list(request):
    """List all rooms"""
    rooms = Room.objects.select_related('building').all()
    buildings = Building.objects.all()
    time_slots = TimeSlot.objects.all().order_by('start_time')
    
    context = {
        'page_title': 'Timetable Management',
        'rooms': rooms,
        'buildings': buildings,
        'time_slots': time_slots,
        'weekdays': ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'],
    }
    return render(request, 'timetable/timetable_list.html', context)


@login_required
@user_passes_test(is_admin)
def room_create(request):
    """Create a new room"""
    if request.method == 'POST':
        try:
            room = Room(
                building_id=request.POST.get('building'),
                room_number=request.POST.get('room_number'),
                name=request.POST.get('name', ''),
                floor=request.POST.get('floor', 1),
                room_type=request.POST.get('room_type'),
                capacity=request.POST.get('capacity', 40),
                has_projector='has_projector' in request.POST,
                has_ac='has_ac' in request.POST,
                has_whiteboard='has_whiteboard' in request.POST,
                has_computer='has_computer' in request.POST,
                has_internet='has_internet' in request.POST,
                description=request.POST.get('description', ''),
            )
            room.save()
            
            messages.success(request, f'Room {room} created successfully!')
            return redirect('timetable:room_list')
        except Exception as e:
            messages.error(request, f'Error creating room: {str(e)}')
    
    buildings = Building.objects.filter(is_active=True)
    context = {
        'page_title': 'Add Room',
        'buildings': buildings,
    }
    return render(request, 'timetable/room_form.html', context)


@login_required
@user_passes_test(is_admin)
def room_update(request, pk):
    """Update a room"""
    room = get_object_or_404(Room, pk=pk)
    
    if request.method == 'POST':
        try:
            room.building_id = request.POST.get('building')
            room.room_number = request.POST.get('room_number')
            room.name = request.POST.get('name', '')
            room.floor = request.POST.get('floor', 1)
            room.room_type = request.POST.get('room_type')
            room.capacity = request.POST.get('capacity', 40)
            room.has_projector = 'has_projector' in request.POST
            room.has_ac = 'has_ac' in request.POST
            room.has_whiteboard = 'has_whiteboard' in request.POST
            room.has_computer = 'has_computer' in request.POST
            room.has_internet = 'has_internet' in request.POST
            room.description = request.POST.get('description', '')
            room.is_active = 'is_active' in request.POST
            room.save()
            
            messages.success(request, f'Room {room} updated successfully!')
            return redirect('timetable:room_list')
        except Exception as e:
            messages.error(request, f'Error updating room: {str(e)}')
    
    buildings = Building.objects.filter(is_active=True)
    context = {
        'page_title': f'Edit {room}',
        'room': room,
        'buildings': buildings,
    }
    return render(request, 'timetable/room_form.html', context)


# TimeSlot Views
@login_required
@user_passes_test(is_admin)
def timeslot_list(request):
    """List all time slots"""
    slots = TimeSlot.objects.all().order_by('day', 'slot_order', 'start_time')
    context = {
        'page_title': 'Time Slots',
        'slots': slots,
    }
    return render(request, 'timetable/timeslot_list.html', context)


@login_required
@user_passes_test(is_admin)
def timeslot_create(request):
    """Create time slots for a day"""
    if request.method == 'POST':
        try:
            day = request.POST.get('day')
            start_times = request.POST.getlist('start_time')
            end_times = request.POST.getlist('end_time')
            orders = request.POST.getlist('slot_order')
            
            for i, start in enumerate(start_times):
                if start and i < len(end_times):
                    TimeSlot.objects.update_or_create(
                        day=day,
                        start_time=start,
                        defaults={
                            'end_time': end_times[i],
                            'slot_order': orders[i] if i < len(orders) else i,
                            'is_break': 'is_break' in request.POST and f'break_{i}' in request.POST,
                        }
                    )
            
            messages.success(request, 'Time slots created successfully!')
            return redirect('timetable:timeslot_list')
        except Exception as e:
            messages.error(request, f'Error creating time slots: {str(e)}')
    
    context = {'page_title': 'Create Time Slots'}
    return render(request, 'timetable/timeslot_form.html', context)


# Timetable Views
@login_required
@user_passes_test(is_admin)
def timetable_list(request):
    """List all timetables"""
    timetables = Timetable.objects.select_related('semester', 'department').all()
    
    context = {
        'page_title': 'Timetables',
        'timetables': timetables,
    }
    return render(request, 'timetable/timetable_list.html', context)


@login_required
@user_passes_test(is_admin)
def timetable_create(request):
    """Create a new timetable"""
    if request.method == 'POST':
        try:
            timetable = Timetable(
                name=request.POST.get('name'),
                semester_id=request.POST.get('semester'),
                department_id=request.POST.get('department') or None,
                level=request.POST.get('level', ''),
                effective_from=request.POST.get('effective_from'),
                effective_to=request.POST.get('effective_to') or None,
                notes=request.POST.get('notes', ''),
            )
            timetable.save()
            
            messages.success(request, f'Timetable {timetable.name} created successfully!')
            return redirect('timetable:timetable_detail', pk=timetable.pk)
        except Exception as e:
            messages.error(request, f'Error creating timetable: {str(e)}')
    
    semesters = Semester.objects.filter(is_active=True)
    departments = Department.objects.filter(is_active=True)
    
    context = {
        'page_title': 'Create Timetable',
        'semesters': semesters,
        'departments': departments,
    }
    return render(request, 'timetable/timetable_form.html', context)


@login_required
@user_passes_test(is_admin)
def timetable_detail(request, pk):
    """View timetable details"""
    timetable = get_object_or_404(Timetable, pk=pk)
    entries = timetable.entries.select_related('course', 'teacher', 'room', 'time_slot').order_by('day', 'time_slot__slot_order')
    
    # Group by day
    days = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday']
    timetable_data = {}
    for day in days:
        timetable_data[day] = entries.filter(day=day)
    
    context = {
        'page_title': f'{timetable.name} - Timetable',
        'timetable': timetable,
        'entries': entries,
        'timetable_data': timetable_data,
        'days': days,
    }
    return render(request, 'timetable/timetable_detail.html', context)


@login_required
@user_passes_test(is_admin)
def timetable_update(request, pk):
    """Update a timetable"""
    timetable = get_object_or_404(Timetable, pk=pk)
    
    if request.method == 'POST':
        try:
            timetable.name = request.POST.get('name')
            timetable.level = request.POST.get('level', '')
            timetable.effective_from = request.POST.get('effective_from')
            timetable.effective_to = request.POST.get('effective_to') or None
            timetable.notes = request.POST.get('notes', '')
            timetable.save()
            
            messages.success(request, f'Timetable {timetable.name} updated successfully!')
            return redirect('timetable:timetable_detail', pk=pk)
        except Exception as e:
            messages.error(request, f'Error updating timetable: {str(e)}')
    
    semesters = Semester.objects.filter(is_active=True)
    departments = Department.objects.filter(is_active=True)
    
    context = {
        'page_title': f'Edit {timetable.name}',
        'timetable': timetable,
        'semesters': semesters,
        'departments': departments,
    }
    return render(request, 'timetable/timetable_form.html', context)


@login_required
@user_passes_test(is_admin)
def timetable_publish(request, pk):
    """Publish a timetable"""
    timetable = get_object_or_404(Timetable, pk=pk)
    
    if request.method == 'POST':
        timetable.status = 'published'
        timetable.is_current = True
        timetable.save()
        
        messages.success(request, f'Timetable {timetable.name} published successfully!')
        return redirect('timetable:timetable_detail', pk=pk)
    
    context = {
        'page_title': f'Publish {timetable.name}',
        'timetable': timetable,
    }
    return render(request, 'timetable/timetable_publish.html', context)


# Timetable Entry Views
@login_required
@user_passes_test(is_admin)
def entry_create(request):
    """Create a new timetable entry"""
    if request.method == 'POST':
        try:
            entry = TimetableEntry(
                timetable_id=request.POST.get('timetable'),
                course_id=request.POST.get('course'),
                teacher_id=request.POST.get('teacher') or None,
                room_id=request.POST.get('room') or None,
                time_slot_id=request.POST.get('time_slot'),
                day=request.POST.get('day'),
                entry_type=request.POST.get('entry_type', 'lecture'),
                start_date=request.POST.get('start_date'),
                end_date=request.POST.get('end_date') or None,
            )
            entry.save()
            
            messages.success(request, 'Timetable entry created successfully!')
            return redirect('timetable:timetable_detail', pk=entry.timetable.pk)
        except Exception as e:
            messages.error(request, f'Error creating entry: {str(e)}')
    
    timetables = Timetable.objects.filter(status='draft')
    courses = Course.objects.filter(status='active')
    teachers = Teacher.objects.filter(status='active')
    rooms = Room.objects.filter(is_active=True)
    time_slots = TimeSlot.objects.filter(is_active=True)
    
    context = {
        'page_title': 'Add Timetable Entry',
        'timetables': timetables,
        'courses': courses,
        'teachers': teachers,
        'rooms': rooms,
        'time_slots': time_slots,
    }
    return render(request, 'timetable/entry_form.html', context)


@login_required
@user_passes_test(is_admin)
def entry_update(request, pk):
    """Update a timetable entry"""
    entry = get_object_or_404(TimetableEntry, pk=pk)
    
    if request.method == 'POST':
        try:
            entry.course_id = request.POST.get('course')
            entry.teacher_id = request.POST.get('teacher') or None
            entry.room_id = request.POST.get('room') or None
            entry.time_slot_id = request.POST.get('time_slot')
            entry.day = request.POST.get('day')
            entry.entry_type = request.POST.get('entry_type', 'lecture')
            entry.save()
            
            messages.success(request, 'Timetable entry updated successfully!')
            return redirect('timetable:timetable_detail', pk=entry.timetable.pk)
        except Exception as e:
            messages.error(request, f'Error updating entry: {str(e)}')
    
    courses = Course.objects.filter(status='active')
    teachers = Teacher.objects.filter(status='active')
    rooms = Room.objects.filter(is_active=True)
    time_slots = TimeSlot.objects.filter(is_active=True)
    
    context = {
        'page_title': 'Edit Timetable Entry',
        'entry': entry,
        'courses': courses,
        'teachers': teachers,
        'rooms': rooms,
        'time_slots': time_slots,
    }
    return render(request, 'timetable/entry_form.html', context)


@login_required
@user_passes_test(is_admin)
def entry_delete(request, pk):
    """Delete a timetable entry"""
    entry = get_object_or_404(TimetableEntry, pk=pk)
    timetable_pk = entry.timetable.pk
    
    if request.method == 'POST':
        entry.delete()
        messages.success(request, 'Timetable entry deleted successfully!')
        return redirect('timetable:timetable_detail', pk=timetable_pk)
    
    context = {
        'page_title': 'Delete Timetable Entry',
        'entry': entry,
    }
    return render(request, 'timetable/entry_confirm_delete.html', context)


# Room Booking Views
@login_required
@user_passes_test(is_teacher_or_admin)
def booking_list(request):
    """List room bookings"""
    bookings = RoomBooking.objects.select_related('room', 'booked_by').all()
    
    context = {
        'page_title': 'Room Bookings',
        'bookings': bookings,
    }
    return render(request, 'timetable/booking_list.html', context)


@login_required
@user_passes_test(is_teacher_or_admin)
def booking_create(request):
    """Create a room booking"""
    if request.method == 'POST':
        try:
            booking = RoomBooking(
                room_id=request.POST.get('room'),
                booked_by=request.user.teacher if hasattr(request.user, 'teacher') else None,
                title=request.POST.get('title'),
                booking_type=request.POST.get('booking_type'),
                start_datetime=request.POST.get('start_datetime'),
                end_datetime=request.POST.get('end_datetime'),
                is_recurring='is_recurring' in request.POST,
                recurrence_pattern=request.POST.get('recurrence_pattern', ''),
                attendees=request.POST.get('attendees', 0),
                purpose=request.POST.get('purpose', ''),
            )
            booking.save()
            
            messages.success(request, 'Room booking created successfully!')
            return redirect('timetable:booking_list')
        except Exception as e:
            messages.error(request, f'Error creating booking: {str(e)}')
    
    rooms = Room.objects.filter(is_active=True)
    context = {
        'page_title': 'Book Room',
        'rooms': rooms,
    }
    return render(request, 'timetable/booking_form.html', context)


@login_required
@user_passes_test(is_admin)
def booking_approve(request, pk):
    """Approve a room booking"""
    booking = get_object_or_404(RoomBooking, pk=pk)
    
    if request.method == 'POST':
        booking.status = 'approved'
        booking.approved_by = request.user.teacher if hasattr(request.user, 'teacher') else None
        booking.save()
        
        messages.success(request, 'Room booking approved!')
        return redirect('timetable:booking_list')
    
    context = {
        'page_title': 'Approve Booking',
        'booking': booking,
    }
    return render(request, 'timetable/booking_approve.html', context)


# Personal Timetable Views
@login_required
def my_timetable(request):
    """View personal timetable"""
    user = request.user
    
    if hasattr(user, 'teacher'):
        entries = TimetableEntry.objects.filter(
            teacher=user.teacher,
            timetable__status='published'
        ).select_related('course', 'room', 'time_slot', 'timetable')
    elif hasattr(user, 'student'):
        from courses.models import CourseEnrollment
        enrolled_courses = CourseEnrollment.objects.filter(
            student=user.student,
            is_active=True
        ).values_list('course', flat=True)
        
        entries = TimetableEntry.objects.filter(
            course_id__in=enrolled_courses,
            timetable__status='published'
        ).select_related('course', 'teacher', 'room', 'time_slot', 'timetable')
    else:
        entries = []
    
    # Group by day
    days = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday']
    timetable_data = {}
    for day in days:
        timetable_data[day] = entries.filter(day=day).order_by('time_slot__slot_order')
    
    context = {
        'page_title': 'My Timetable',
        'entries': entries,
        'timetable_data': timetable_data,
        'days': days,
    }
    return render(request, 'timetable/my_timetable.html', context)
