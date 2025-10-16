from django.db import models
from schools.models import School
from users.models import User, Teacher, Student

class Subject(models.Model):
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=10, unique=True)
    description = models.TextField(blank=True)
    school = models.ForeignKey(School, on_delete=models.CASCADE)
    
    def __str__(self):
        return f"{self.name} ({self.code})"

class ClassLevel(models.Model):
    name = models.CharField(max_length=50)  # e.g., "Grade 10", "Primary 5"
    level = models.IntegerField()  # for ordering
    school = models.ForeignKey(School, on_delete=models.CASCADE)
    
    class Meta:
        ordering = ['level']
    
    def __str__(self):
        return self.name

class Assignment(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE)
    due_date = models.DateTimeField()
    max_score = models.IntegerField(default=100)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.title

class StudentAssignment(models.Model):
    assignment = models.ForeignKey(Assignment, on_delete=models.CASCADE)
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
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
    
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    exam_type = models.CharField(max_length=20, choices=EXAM_TYPES)
    score = models.IntegerField()
    max_score = models.IntegerField(default=100)
    date_taken = models.DateField()
    recorded_by = models.ForeignKey(Teacher, on_delete=models.CASCADE)
    
    class Meta:
        unique_together = ['student', 'subject', 'exam_type', 'date_taken']
    
    def __str__(self):
        return f"{self.student} - {self.subject} - {self.get_exam_type_display()}"
    
class FeeStructure(models.Model):
    school = models.ForeignKey(School, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)  # e.g., "Term 1 Fees 2024"
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    due_date = models.DateField()
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return f"{self.name} - {self.school.name}"

class StudentFee(models.Model):
    PAYMENT_STATUS = (
        ('pending', 'Pending'),
        ('partial', 'Partial'),
        ('paid', 'Paid'),
        ('overdue', 'Overdue'),
    )
    
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    fee_structure = models.ForeignKey(FeeStructure, on_delete=models.CASCADE)
    amount_due = models.DecimalField(max_digits=10, decimal_places=2)
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS, default='pending')
    due_date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    def balance(self):
        return self.amount_due - self.amount_paid
    
    def __str__(self):
        return f"{self.student} - {self.fee_structure.name}"