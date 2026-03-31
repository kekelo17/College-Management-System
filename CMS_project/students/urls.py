from django.urls import path
from . import views

app_name = 'students'

urlpatterns = [
    # Student CRUD
    path('', views.student_list, name='student_list'),
    path('create/', views.student_create, name='student_create'),
    path('<int:pk>/', views.student_detail, name='student_detail'),
    path('<int:pk>/update/', views.student_update, name='student_update'),
    path('<int:pk>/delete/', views.student_delete, name='student_delete'),
    path('<int:pk>/profile/', views.student_profile, name='student_profile'),
    
    # Academic Year
    path('academic-year/', views.academic_year_list, name='academic_year_list'),
    path('academic-year/create/', views.academic_year_create, name='academic_year_create'),
    path('academic-year/<int:pk>/update/', views.academic_year_update, name='academic_year_update'),
    
    # Semester
    path('semester/', views.semester_list, name='semester_list'),
    path('semester/create/', views.semester_create, name='semester_create'),
    path('semester/<int:pk>/update/', views.semester_update, name='semester_update'),
    
    # Guardian
    path('<int:student_pk>/guardian/add/', views.guardian_create, name='guardian_create'),
    path('guardian/<int:pk>/update/', views.guardian_update, name='guardian_update'),
    
    # Documents
    path('<int:student_pk>/document/add/', views.document_create, name='document_create'),
    path('document/<int:pk>/delete/', views.document_delete, name='document_delete'),
    
    # Class Assignment
    path('<int:student_pk>/class/add/', views.student_class_add, name='student_class_add'),
    
    # Bulk Operations
    path('import/', views.student_import, name='student_import'),
    path('export/', views.student_export, name='student_export'),
]
