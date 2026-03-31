from django.urls import path
from . import views

app_name = 'results'

urlpatterns = [
    # Exam
    path('exam/', views.exam_list, name='exam_list'),
    path('exam/create/', views.exam_create, name='exam_create'),
    path('exam/<int:pk>/', views.exam_detail, name='exam_detail'),
    path('exam/<int:pk>/update/', views.exam_update, name='exam_update'),
    path('exam/<int:pk>/delete/', views.exam_delete, name='exam_delete'),
    
    # Result
    path('', views.result_list, name='result_list'),
    path('create/', views.result_create, name='result_create'),
    path('<int:pk>/', views.result_detail, name='result_detail'),
    path('<int:pk>/update/', views.result_update, name='result_update'),
    
    # Bulk Result Entry
    path('bulk-entry/', views.bulk_result_entry, name='bulk_result_entry'),
    path('bulk-upload/', views.bulk_result_upload, name='bulk_result_upload'),
    
    # Semester Result
    path('semester-result/', views.semester_result_list, name='semester_result_list'),
    path('semester-result/<int:pk>/', views.semester_result_detail, name='semester_result_detail'),
    path('semester-result/<int:pk>/generate/', views.generate_semester_result, name='generate_semester_result'),
    
    # Grade
    path('grade/', views.grade_list, name='grade_list'),
    path('grade/create/', views.grade_create, name='grade_create'),
    path('grade/<int:pk>/update/', views.grade_update, name='grade_update'),
    
    # Assessment
    path('assessment/', views.assessment_list, name='assessment_list'),
    path('assessment/create/', views.assessment_create, name='assessment_create'),
    path('assessment/<int:pk>/', views.assessment_detail, name='assessment_detail'),
    path('assessment/<int:pk>/score/', views.assessment_score_entry, name='assessment_score_entry'),
    
    # Student Results
    path('student/', views.student_results, name='student_results'),
    path('student/transcript/', views.student_transcript, name='student_transcript'),
]
