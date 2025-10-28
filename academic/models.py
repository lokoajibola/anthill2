from django.db import models
from django.core.validators import FileExtensionValidator
from django.conf import settings


class Subject(models.Model):
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=10, unique=True)
    description = models.TextField(blank=True)
    category = models.CharField(max_length=50, blank=True)
    
    def __str__(self):
        return f"{self.name} ({self.code})"

class ClassLevel(models.Model):
    LEVEL_CHOICES = (
        ('primary_1', 'Primary 1'),
        ('primary_2', 'Primary 2'), 
        ('primary_3', 'Primary 3'),
        ('primary_4', 'Primary 4'),
        ('primary_5', 'Primary 5'),
        ('primary_6', 'Primary 6'),
        ('jss_1', 'JSS 1'),
        ('jss_2', 'JSS 2'),
        ('jss_3', 'JSS 3'),
        ('ss_1', 'SS 1'),
        ('ss_2', 'SS 2'),
        ('ss_3', 'SS 3'),
    )
    
    name = models.CharField(max_length=50)
    level = models.CharField(max_length=20, choices=LEVEL_CHOICES)  # Change to CharField
    description = models.TextField(blank=True)
    school = models.ForeignKey('schools.School', on_delete=models.CASCADE, null=True, related_name='academic_classes')
    
    class Meta:
        ordering = ['level']
        unique_together = ['name', 'school']
    
    def __str__(self):
        if self.school:
            return f"{self.name} - {self.school.name}"
        return self.name

class ClassSubject(models.Model):
    class_level = models.ForeignKey(ClassLevel, on_delete=models.CASCADE)
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    is_compulsory = models.BooleanField(default=True)
    teacher = models.ForeignKey('users.Teacher', on_delete=models.SET_NULL, null=True, blank=True)  # String reference
    
    class Meta:
        unique_together = ['class_level', 'subject']
    
    def __str__(self):
        return f"{self.class_level.name} - {self.subject.name}"

class Assignment(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    teacher = models.ForeignKey('users.Teacher', on_delete=models.CASCADE)
    due_date = models.DateTimeField()
    max_score = models.IntegerField(default=100)
    created_at = models.DateTimeField(auto_now_add=True)
    assignment_file = models.FileField(upload_to='assignments/', blank=True, null=True, validators=[FileExtensionValidator(allowed_extensions=['pdf', 'doc', 'docx', 'txt', 'zip'])])
    
    def __str__(self):
        return self.title

class StudentAssignment(models.Model):
    assignment = models.ForeignKey('Assignment', on_delete=models.CASCADE)
    student = models.ForeignKey('users.Student', on_delete=models.CASCADE)
    submitted_file = models.FileField(
        upload_to='submitted_assignments/', 
        blank=True, 
        null=True, 
        validators=[FileExtensionValidator(allowed_extensions=['pdf', 'doc', 'docx', 'txt', 'zip', 'jpg', 'png'])]
    )
    submission_date = models.DateTimeField(null=True, blank=True)  # This field is missing
    score = models.FloatField(null=True, blank=True)
    feedback = models.TextField(blank=True)
    is_submitted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.student} - {self.assignment}"


class Result(models.Model):
    EXAM_TYPES = (
        ('test', 'Test'),
        ('assignment', 'Assignment'),
        ('exam', 'Exam'),
    )
    
    student = models.ForeignKey('users.Student', on_delete=models.CASCADE)  # String reference
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    exam_type = models.CharField(max_length=20, choices=EXAM_TYPES)
    score = models.IntegerField()
    max_score = models.IntegerField(default=100)
    date_taken = models.DateField()
    recorded_by = models.ForeignKey('users.Teacher', on_delete=models.CASCADE)  # String reference
    
    class Meta:
        unique_together = ['student', 'subject', 'exam_type', 'date_taken']
    
    def __str__(self):
        return f"{self.student} - {self.subject} - {self.get_exam_type_display()}"
    
class FeeStructure(models.Model):
    class_level = models.ForeignKey('ClassLevel', on_delete=models.CASCADE, related_name='fee_structures')
    academic_year = models.CharField(max_length=20)
    tuition_fee = models.DecimalField(max_digits=10, decimal_places=2)
    development_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    other_charges = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_fee = models.DecimalField(max_digits=10, decimal_places=2)
    
    class Meta:
        unique_together = ['class_level', 'academic_year']
    
    
