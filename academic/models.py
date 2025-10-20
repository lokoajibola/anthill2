from django.db import models

class Subject(models.Model):
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=10, unique=True)
    description = models.TextField(blank=True)
    category = models.CharField(max_length=50, blank=True)
    
    def __str__(self):
        return f"{self.name} ({self.code})"

class ClassLevel(models.Model):
    name = models.CharField(max_length=50)
    level = models.IntegerField()
    school = models.ForeignKey('schools.School', on_delete=models.CASCADE, null=True)  # String reference
    
    class Meta:
        ordering = ['level']
        unique_together = ['name', 'school']
    
    def __str__(self):
        return f"{self.name} - {self.school.name}"

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
    description = models.TextField()
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    teacher = models.ForeignKey('users.Teacher', on_delete=models.CASCADE)  # String reference
    due_date = models.DateTimeField()
    max_score = models.IntegerField(default=100)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.title

class StudentAssignment(models.Model):
    assignment = models.ForeignKey(Assignment, on_delete=models.CASCADE)
    student = models.ForeignKey('users.Student', on_delete=models.CASCADE)  # String reference
    submitted_file = models.FileField(upload_to='assignments/', blank=True)
    submitted_text = models.TextField(blank=True)
    submitted_at = models.DateTimeField(null=True, blank=True)
    score = models.IntegerField(null=True, blank=True)
    is_submitted = models.BooleanField(default=False)
    
    class Meta:
        unique_together = ['assignment', 'student']
    
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
    
    
