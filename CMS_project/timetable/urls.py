from django.urls import path
from . import views

app_name = 'timetable'

urlpatterns = [
    # Building
    path('building/', views.building_list, name='building_list'),
    path('building/create/', views.building_create, name='building_create'),
    path('building/<int:pk>/update/', views.building_update, name='building_update'),
    
    # Room
    path('room/', views.room_list, name='room_list'),
    path('room/create/', views.room_create, name='room_create'),
    path('room/<int:pk>/update/', views.room_update, name='room_update'),
    
    # Time Slot
    path('time-slot/', views.timeslot_list, name='timeslot_list'),
    path('time-slot/create/', views.timeslot_create, name='timeslot_create'),
    
    # Timetable
    path('', views.timetable_list, name='timetable_list'),
    path('create/', views.timetable_create, name='timetable_create'),
    path('<int:pk>/', views.timetable_detail, name='timetable_detail'),
    path('<int:pk>/update/', views.timetable_update, name='timetable_update'),
    path('<int:pk>/publish/', views.timetable_publish, name='timetable_publish'),
    
    # Timetable Entry
    path('entry/create/', views.entry_create, name='entry_create'),
    path('entry/<int:pk>/update/', views.entry_update, name='entry_update'),
    path('entry/<int:pk>/delete/', views.entry_delete, name='entry_delete'),
    
    # Room Booking
    path('booking/', views.booking_list, name='booking_list'),
    path('booking/create/', views.booking_create, name='booking_create'),
    path('booking/<int:pk>/approve/', views.booking_approve, name='booking_approve'),
    
    # Student/Teacher Timetable
    path('my-timetable/', views.my_timetable, name='my_timetable'),
]
