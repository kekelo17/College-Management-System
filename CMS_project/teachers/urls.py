from django.urls import path
from . import views

app_name = 'teachers'

urlpatterns = [
    # Teacher CRUD
    path('', views.teacher_list, name='teacher_list'),
    path('create/', views.teacher_create, name='teacher_create'),
    path('<int:pk>/', views.teacher_detail, name='teacher_detail'),
    path('<int:pk>/update/', views.teacher_update, name='teacher_update'),
    path('<int:pk>/delete/', views.teacher_delete, name='teacher_delete'),
    path('<int:pk>/profile/', views.teacher_profile, name='teacher_profile'),
    
    # Qualification
    path('<int:teacher_pk>/qualification/add/', views.qualification_create, name='qualification_create'),
    path('qualification/<int:pk>/delete/', views.qualification_delete, name='qualification_delete'),
    
    # Experience
    path('<int:teacher_pk>/experience/add/', views.experience_create, name='experience_create'),
    path('experience/<int:pk>/delete/', views.experience_delete, name='experience_delete'),
    
    # Document
    path('<int:teacher_pk>/document/add/', views.teacher_document_create, name='document_create'),
    path('document/<int:pk>/delete/', views.teacher_document_delete, name='document_delete'),
    
    # Leave
    path('leave/', views.teacher_leave_list, name='leave_list'),
    path('leave/apply/', views.leave_apply, name='leave_apply'),
    path('leave/<int:pk>/', views.leave_detail, name='leave_detail'),
    path('leave/<int:pk>/approve/', views.leave_approve, name='leave_approve'),
    path('leave/<int:pk>/reject/', views.leave_reject, name='leave_reject'),
    
    # Bulk Operations
    path('import/', views.teacher_import, name='teacher_import'),
    path('export/', views.teacher_export, name='teacher_export'),
]
