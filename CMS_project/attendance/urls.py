from django.urls import path
from . import views

app_name = 'attendance'

urlpatterns = [
    # Attendance Session
    path('', views.attendance_list, name='attendance_list'),
    path('create/', views.attendance_create, name='attendance_create'),
    path('<int:pk>/', views.attendance_detail, name='attendance_detail'),
    path('<int:pk>/update/', views.attendance_update, name='attendance_update'),
    path('<int:pk>/delete/', views.attendance_delete, name='attendance_delete'),
    
    # Mark Attendance
    path('<int:pk>/mark/', views.attendance_mark, name='attendance_mark'),
    path('<int:pk>/mark-all/', views.attendance_mark_all, name='attendance_mark_all'),
    
    # Record Management
    path('record/<int:pk>/update/', views.record_update, name='record_update'),
    
    # Student Attendance
    path('student/', views.student_attendance, name='student_attendance'),
    path('student/report/', views.student_attendance_report, name='student_attendance_report'),
    
    # Leave/Excuse
    path('leave/', views.leave_list, name='leave_list'),
    path('leave/apply/', views.leave_apply, name='leave_apply'),
    path('leave/<int:pk>/', views.leave_detail, name='leave_detail'),
    path('leave/<int:pk>/approve/', views.leave_approve, name='leave_approve'),
    path('leave/<int:pk>/reject/', views.leave_reject, name='leave_reject'),
    
    # Summary
    path('summary/', views.attendance_summary, name='attendance_summary'),
]
