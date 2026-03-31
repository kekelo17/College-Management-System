from django.urls import path
from django.views.generic import TemplateView
from . import views

app_name = 'core'

urlpatterns = [
    # Landing page (root URL)
    path('', views.landing_page, name='landing'),
    
    # Dashboard
    path('dashboard/', views.dashboard, name='dashboard'),
    path('admin/dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('teacher/dashboard/', views.teacher_dashboard, name='teacher_dashboard'),
    path('student/dashboard/', views.student_dashboard, name='student_dashboard'),
    path('analytics/', views.analytics, name='analytics'),
    path('api/chart-data/', views.chart_data, name='chart_data'),
]
