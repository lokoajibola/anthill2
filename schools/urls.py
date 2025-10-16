from django.urls import path
from . import views

app_name = 'schools'

urlpatterns = [
    path('dashboard/', views.school_dashboard, name='dashboard'),
    path('manage-users/', views.manage_users, name='manage_users'),
    path('create-user/<str:user_type>/', views.create_user, name='create_user'),
    path('edit-user/<int:user_id>/', views.edit_user, name='edit_user'),
    path('delete-user/<int:user_id>/', views.delete_user, name='delete_user'),
    path('assign-subjects/<int:teacher_id>/', views.assign_subjects_to_teacher, name='assign_subjects'),  # Add this line

    path('search/', views.search_entities, name='search'),
    path('homepage/edit/', views.edit_school_homepage, name='edit_homepage'),
    path('fees/', views.fee_management, name='fee_management'),
    path('analytics/', views.school_analytics, name='analytics'),
    path('payments/', views.payment_history, name='payment_history'),
    path('upgrade/', views.upgrade_subscription, name='upgrade_subscription'),
    path('admin-analytics/', views.admin_analytics, name='admin_analytics'),
    path('<int:school_id>/', views.school_homepage, name='school_homepage'),
]