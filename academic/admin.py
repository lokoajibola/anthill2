from django.contrib import admin
from .models import Subject, ClassLevel, Assignment, StudentAssignment, Result

@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'school']
    list_filter = ['school']
    search_fields = ['name', 'code']

@admin.register(ClassLevel)
class ClassLevelAdmin(admin.ModelAdmin):
    list_display = ['name', 'level', 'school']
    list_filter = ['school']
    ordering = ['level']

@admin.register(Assignment)
class AssignmentAdmin(admin.ModelAdmin):
    list_display = ['title', 'subject', 'teacher', 'due_date', 'max_score']
    list_filter = ['subject', 'teacher']

@admin.register(StudentAssignment)
class StudentAssignmentAdmin(admin.ModelAdmin):
    list_display = ['student', 'assignment', 'is_submitted', 'score']
    list_filter = ['is_submitted']

@admin.register(Result)
class ResultAdmin(admin.ModelAdmin):
    list_display = ['student', 'subject', 'exam_type', 'score', 'max_score', 'date_taken']
    list_filter = ['exam_type', 'subject']