from django.urls import path
from . import views

app_name = 'users'

urlpatterns = [
    path('register/', views.register_school, name='register'),
    path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),
    path('teacher/dashboard/', views.teacher_dashboard, name='teacher_dashboard'),
    path('student/dashboard/', views.student_dashboard, name='student_dashboard'),
    path('profile/edit/', views.edit_profile, name='edit_profile'),
]