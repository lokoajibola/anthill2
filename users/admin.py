from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, Teacher, Student

@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ['username', 'email', 'first_name', 'last_name', 'user_type', 'is_staff']
    list_filter = ['user_type', 'is_staff', 'is_active']
    fieldsets = UserAdmin.fieldsets + (
        ('Custom Fields', {'fields': ('user_type', 'phone', 'profile_picture')}),
    )

@admin.register(Teacher)
class TeacherAdmin(admin.ModelAdmin):
    list_display = ['user', 'school', 'date_joined']
    list_filter = ['school']

@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ['user', 'school', 'admission_number', 'class_level']
    list_filter = ['school', 'class_level']
    search_fields = ['admission_number', 'user__first_name', 'user__last_name']