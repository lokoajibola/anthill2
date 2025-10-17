from django.urls import path
from . import views

app_name = 'academic'

urlpatterns = [
    # Teacher URLs
    path('teacher/subjects/', views.teacher_subjects, name='teacher_subjects'),
    path('teacher/assignments/', views.teacher_assignments, name='teacher_assignments'),
    path('teacher/assignments/create/', views.create_assignment, name='create_assignment'),
    path('teacher/upload-scores/', views.upload_scores, name='upload_scores'),
    path('teacher/students/', views.teacher_students, name='teacher_students'),  # Add this line
    
    # Student URLs
    path('student/assignments/', views.student_assignments, name='student_assignments'),
    path('student/assignments/<int:assignment_id>/submit/', views.submit_assignment, name='submit_assignment'),
    path('student/results/', views.student_results, name='student_results'),
    path('student/fees/', views.student_fees, name='student_fees'),
]