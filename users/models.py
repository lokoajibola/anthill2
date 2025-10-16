from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    USER_TYPE_CHOICES = (
        ('super_admin', 'Super Admin'),
        ('senior_admin', 'Senior School Admin'),
        ('junior_admin', 'Junior School Admin'),
        ('teacher', 'Teacher'),
        ('student', 'Student'),
    )
    
    user_type = models.CharField(max_length=20, choices=USER_TYPE_CHOICES)
    phone = models.CharField(max_length=15, blank=True)
    profile_picture = models.ImageField(upload_to='profiles/', blank=True)
    
    def __str__(self):
        return f"{self.username} ({self.get_user_type_display()})"
    
class Teacher(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    school = models.ForeignKey('schools.School', on_delete=models.CASCADE)
    subjects = models.ManyToManyField('academic.Subject', blank=True)
    date_joined = models.DateField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.user.get_full_name()} - {self.school.name}"

class Student(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    school = models.ForeignKey('schools.School', on_delete=models.CASCADE)
    admission_number = models.CharField(max_length=20, unique=True)
    class_level = models.ForeignKey('academic.ClassLevel', on_delete=models.SET_NULL, null=True)
    date_admitted = models.DateField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.user.get_full_name()} - {self.admission_number}"