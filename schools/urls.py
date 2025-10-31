from django.urls import path
from . import views

app_name = 'schools'

urlpatterns = [
    path('dashboard/', views.school_dashboard, name='dashboard'),
    path('manage-users/', views.manage_users, name='manage_users'),
    path('create-user/<str:user_type>/', views.create_user, name='create_user'),
    path('edit-user/<int:user_id>/', views.edit_user, name='edit_user'),
    # path('delete-user/<int:user_id>/', views.delete_user, name='delete_user'),
    path('delete-user/<str:user_type>/<int:user_id>/', views.delete_user, name='delete_user'),
    
    path('fees/manage/', views.manage_fees, name='manage_fees'),
    path('add-article/', views.add_article, name='add_article'),
    path('manage-about/', views.manage_about, name='manage_about'),
    path('make-payment/', views.make_payment, name='make_payment'),
    # path('update-about/', views.update_about, name='update_about'),
    
    # Move user_profile above school_homepage
    path('user-profile/<str:user_type>/<int:user_id>/', views.user_profile, name='user_profile'),
    path('fees/student-search/', views.student_fee_search, name='student_fee_search'),
    path('fees/student/<int:student_id>/', views.student_fee_details, name='student_fee_details'),
    path('fees/analytics/', views.fee_analytics, name='fee_analytics'),
    path('create-subject/', views.create_subject, name='create_subject'),
    # path('manage-about/', views.manage_about, name='manage_about'),
    path('gallery/', views.manage_gallery, name='manage_gallery'),
    path('gallery/delete/<int:image_id>/', views.delete_gallery_image, name='delete_gallery_image'),
    path('admission/', views.manage_admission, name='manage_admission'),
    path('search/', views.search_entities, name='search'),
    path('classes/', views.manage_classes, name='manage_classes'),
    path('classes/create/', views.create_class, name='create_class'),
    path('classes/<int:class_id>/subjects/', views.class_subjects, name='class_subjects'),
    path('classes/<int:class_id>/students/', views.manage_class_students, name='manage_class_students'),
    path('homepage/edit/', views.edit_school_homepage, name='edit_homepage'),
    path('fees/management/', views.fee_management, name='fee_management'),
    path('fees/create/', views.create_fees, name='create_fees'),
    path('manage-news/', views.manage_news, name='manage_news'),
    path('article/<int:article_id>/edit/', views.edit_article, name='edit_article'),
    path('article/<int:article_id>/delete/', views.delete_article, name='delete_article'),
    
    # path('fees/', views.fee_management, name='fee_management'),
    path('verify-payment/', views.verify_payment, name='verify_payment'),
    path('analytics/', views.school_analytics, name='analytics'),
    path('payments/', views.payment_history, name='payment_history'),
    path('upgrade/', views.upgrade_subscription, name='upgrade_subscription'),
    path('admin-analytics/', views.admin_analytics, name='admin_analytics'),
    # Move school_homepage to the bottom since it's a catch-all
    path('mark-fee-paid/<int:student_id>/', views.mark_fee_paid, name='mark_fee_paid'),
    path('classes/<int:class_id>/teachers/', views.manage_class_teachers, name='manage_class_teachers'),
    path('<int:school_id>/', views.school_homepage, name='school_homepage'),
    
    
]