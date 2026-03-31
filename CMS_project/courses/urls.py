from django.urls import path
from . import views

app_name = 'courses'

urlpatterns = [
    # Department
    path('department/', views.department_list, name='department_list'),
    path('department/create/', views.department_create, name='department_create'),
    path('department/<int:pk>/', views.department_detail, name='department_detail'),
    path('department/<int:pk>/update/', views.department_update, name='department_update'),
    path('department/<int:pk>/delete/', views.department_delete, name='department_delete'),
    
    # Course
    path('', views.course_list, name='course_list'),
    path('create/', views.course_create, name='course_create'),
    path('<int:pk>/', views.course_detail, name='course_detail'),
    path('<int:pk>/update/', views.course_update, name='course_update'),
    path('<int:pk>/delete/', views.course_delete, name='course_delete'),
    
    # Enrollment
    path('enrollment/', views.enrollment_list, name='enrollment_list'),
    path('enrollment/create/', views.enrollment_create, name='enrollment_create'),
    path('enrollment/<int:pk>/update/', views.enrollment_update, name='enrollment_update'),
    path('enrollment/<int:pk>/delete/', views.enrollment_delete, name='enrollment_delete'),
    
    # Subject
    path('<int:course_pk>/subject/add/', views.subject_create, name='subject_create'),
    path('subject/<int:pk>/update/', views.subject_update, name='subject_update'),
    path('subject/<int:pk>/delete/', views.subject_delete, name='subject_delete'),
    
    # Prerequisite
    path('<int:course_pk>/prerequisite/add/', views.prerequisite_add, name='prerequisite_add'),
    path('prerequisite/<int:pk>/delete/', views.prerequisite_delete, name='prerequisite_delete'),
]
