from django.urls import path
from . import views

app_name = 'academic'

urlpatterns = [
    # ===== TEACHER URLS =====
    path('teacher/subjects/', views.teacher_subjects, name='teacher_subjects'),
    path('teacher/assignments/', views.teacher_assignments, name='teacher_assignments'),
    path('teacher/assignments/create/', views.create_assignment, name='create_assignment'),
    path('teacher/assignments/<int:assignment_id>/edit/', views.edit_assignment, name='edit_assignment'),
    
    path('upload-scores/', views.upload_scores, name='upload_scores'),
    path('teacher/view-scores/', views.view_scores, name='view_scores'),
    path('teacher/students/', views.teacher_students, name='teacher_students'),
    path('view-results/', views.view_results, name='view_results'),
    path('edit-result/<int:result_id>/', views.edit_result, name='edit_result'),
    
    
    
    # ===== STUDENT URLS =====
    path('student/dashboard/', views.student_dashboard, name='student_dashboard'),
    path('assignments/', views.student_assignments, name='student_assignments'),
    path('assignments/<int:assignment_id>/', views.assignment_detail, name='assignment_detail'),
    path('assignments/submit/<int:student_assignment_id>/', views.submit_assignment, name='submit_assignment'),
    path('student/results/', views.student_results, name='student_results'),  # Student's own results
    path('student/fees/', views.student_fees, name='student_fees'),
    
    # ===== ADMIN/OTHER URLS =====
    path('student/results/<int:student_id>/', views.student_results_admin, name='student_results_admin'),  # Admin viewing any student
    
    # ===== API ENDPOINTS =====
    path('api/class-subjects/<int:class_id>/', views.api_class_subjects, name='api_class_subjects'),
    path('api/class-students/<int:class_id>/', views.api_class_students, name='api_class_students'),
    path('api/students-by-class-subject/', views.students_by_class_subject, name='students_by_class_subject'),
    
    # ===== TEST/DEBUG URLS =====
    path('upload-scores-test/', views.upload_scores_test, name='upload_scores_test'),
]