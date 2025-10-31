from django.contrib.auth.models import AbstractUser
from django.db import models
from schools.models import School
from django.core.exceptions import ValidationError

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
    profile_picture = models.ImageField(upload_to='profiles/', blank=True, null=True)
    city = models.CharField(max_length=100, blank=True)
    lga = models.CharField(max_length=100, blank=True)
    address = models.TextField(blank=True)
    
    school = models.ForeignKey(
        School, 
        on_delete=models.CASCADE, 
        related_name='users',
        null=True,
        blank=True
    )
    
    class Meta:
        unique_together = ['school', 'username']  # Username unique per school
    
    def __str__(self):
        if self.school:
            return f"{self.username} - {self.school.name} ({self.get_user_type_display()})"
        return f"{self.username} ({self.get_user_type_display()})"
    
    def save(self, *args, **kwargs):
        # Ensure super_admins don't have a school
        if self.user_type == 'super_admin':
            self.school = None
        
        # Validate that non-super_admin users have a school
        # if self.user_type != 'super_admin' and not self.school:
            # raise ValidationError(f"{self.get_user_type_display()} must be associated with a school.")
        
        super().save(*args, **kwargs)
    
    def clean(self):
        """Additional validation"""
        from django.core.exceptions import ValidationError
        
        # Check username uniqueness within school
        if self.school:
            existing_user = User.objects.filter(
                school=self.school, 
                username=self.username
            ).exclude(pk=self.pk).first()
            
            if existing_user:
                raise ValidationError({
                    'username': f'Username "{self.username}" already exists in {self.school.name}.'
                })
        
        # Super admin validation
        if self.user_type == 'super_admin' and self.school:
            raise ValidationError({
                'school': 'Super Admin cannot be associated with a school.'
            })
    
    @property
    def is_super_admin(self):
        return self.user_type == 'super_admin'
    
    @property 
    def is_school_admin(self):
        return self.user_type in ['senior_admin', 'junior_admin']
    
    @property
    def is_staff_member(self):
        return self.user_type in ['senior_admin', 'junior_admin', 'teacher']

class Teacher(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    school = models.ForeignKey('schools.School', on_delete=models.CASCADE) #, null = True)  # String reference
    subjects = models.ManyToManyField('academic.Subject', blank=True)  # String reference
    date_joined = models.DateField(auto_now_add=True)
    
    date_of_birth = models.DateField(null=True, blank=True)
    allergies = models.TextField(blank=True)
    health_history = models.TextField(blank=True)
    blood_group = models.CharField(max_length=5, blank=True)
    genotype = models.CharField(max_length=5, blank=True)
    home_address = models.TextField(blank=True)
    emergency_contact = models.CharField(max_length=15, blank=True)
    disciplinary_record = models.TextField(blank=True)
    extra_curricular = models.TextField(blank=True)
    sports_house = models.CharField(max_length=50, blank=True)
    awards = models.TextField(blank=True)
    position = models.CharField(max_length=50, blank=True)

    def __str__(self):
        return f"{self.user.get_full_name()} - {self.school.name}"

class Student(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    school = models.ForeignKey('schools.School', on_delete=models.CASCADE, null=True)  # String reference
    admission_number = models.CharField(max_length=20, unique=True)
    class_level = models.ForeignKey('academic.ClassLevel', on_delete=models.SET_NULL, null=True, blank=True)  # String reference
    date_admitted = models.DateField(auto_now_add=True)
    elective_subjects = models.ManyToManyField('academic.Subject', blank=True, related_name='elective_students')  # String reference
    
    date_of_birth = models.DateField(null=True, blank=True)
    allergies = models.TextField(blank=True)
    health_history = models.TextField(blank=True)
    blood_group = models.CharField(max_length=5, blank=True)
    genotype = models.CharField(max_length=5, blank=True)
    home_address = models.TextField(blank=True)
    emergency_contact = models.CharField(max_length=15, blank=True)
    disciplinary_record = models.TextField(blank=True)
    extra_curricular = models.TextField(blank=True)
    sports_house = models.CharField(max_length=50, blank=True)
    awards = models.TextField(blank=True)
    position = models.CharField(max_length=50, blank=True)

    def __str__(self):
        return f"{self.user.get_full_name()} - {self.admission_number}"