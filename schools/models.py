from django.db import models

class School(models.Model):
    SCHOOL_TYPES = (
        ('primary', 'Primary School'),
        ('secondary', 'Secondary School'),
        ('combined', 'Combined School'),
    )
    
    SUBSCRIPTION_TYPES = (
        ('basic', 'Basic'),
        ('pro', 'Pro'),
        ('enterprise', 'Enterprise'),
    )
    
    name = models.CharField(max_length=200)
    logo = models.ImageField(upload_to='schools/logos/', blank=True)
    motto = models.CharField(max_length=300, blank=True)
    about_text = models.TextField(blank=True, null=True)
    vision = models.TextField(blank=True)
    mission = models.TextField(blank=True)
    primary_color = models.CharField(max_length=7, default='#000000')
    school_type = models.CharField(max_length=20, choices=SCHOOL_TYPES)
    subscription_type = models.CharField(max_length=20, choices=SUBSCRIPTION_TYPES)
    phone = models.CharField(max_length=15)
    email = models.EmailField()
    address = models.TextField()
    city = models.CharField(max_length=100)
    lga = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.name

class SchoolAdmin(models.Model):
    school = models.ForeignKey(School, on_delete=models.CASCADE, null = True)
    user = models.OneToOneField('users.User', on_delete=models.CASCADE)  # String reference
    is_senior = models.BooleanField(default=False)
    
    class Meta:
        unique_together = ['school', 'is_senior']

class Subscription(models.Model):
    school = models.OneToOneField(School, on_delete=models.CASCADE)
    start_date = models.DateField()
    end_date = models.DateField()
    is_active = models.BooleanField(default=True)
    auto_renew = models.BooleanField(default=True)
    
    def is_expired(self):
        from django.utils import timezone
        return timezone.now().date() > self.end_date
    
    def days_remaining(self):
        from django.utils import timezone
        return (self.end_date - timezone.now().date()).days
    
    def __str__(self):
        return f"{self.school.name} - {self.school.get_subscription_type_display()}"

class Payment(models.Model):
    PAYMENT_STATUS = (
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded'),
    )
    
    school = models.ForeignKey(School, on_delete=models.CASCADE, null = True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_date = models.DateTimeField(auto_now_add=True)
    due_date = models.DateField()
    status = models.CharField(max_length=20, choices=PAYMENT_STATUS, default='pending')
    transaction_id = models.CharField(max_length=100, blank=True)
    description = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-payment_date']
    
    def __str__(self):
        return f"{self.school.name} - ${self.amount} - {self.status}"

class Article(models.Model):
    school = models.ForeignKey(School, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    content = models.TextField()
    author = models.ForeignKey('users.User', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class GalleryImage(models.Model):
    school = models.ForeignKey(School, on_delete=models.CASCADE)
    image = models.ImageField(upload_to='gallery/')
    title = models.CharField(max_length=100)
    description = models.TextField(blank=True)  # Change to blank=True
    uploaded_at = models.DateTimeField(auto_now_add=True)

class AdmissionInfo(models.Model):
    school = models.OneToOneField(School, on_delete=models.CASCADE)
    requirements = models.TextField()
    process = models.TextField()
    fees = models.TextField()
    contact_info = models.TextField()
    updated_at = models.DateTimeField(auto_now=True)

# Fee models - ADD THESE


class StudentFee(models.Model):
    PAYMENT_STATUS = (
        ('pending', 'Pending'),
        ('partial', 'Partial'),
        ('paid', 'Paid'),
        ('overdue', 'Overdue'),
    )
    
    student = models.ForeignKey('users.Student', on_delete=models.CASCADE)  # String reference
    fee_structure = models.ForeignKey('academic.FeeStructure', on_delete=models.CASCADE)
    amount_due = models.DecimalField(max_digits=10, decimal_places=2)
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS, default='pending')
    due_date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    def balance(self):
        return self.amount_due - self.amount_paid
    
    def __str__(self):
        return f"{self.student.user.get_full_name()} - {self.fee_structure.name}"

class FeePayment(models.Model):
    student_fee = models.ForeignKey(StudentFee, on_delete=models.CASCADE)
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2)
    payment_date = models.DateTimeField(auto_now_add=True)
    payment_method = models.CharField(max_length=50, default='Cash')
    receipt_number = models.CharField(max_length=50, unique=True)
    recorded_by = models.ForeignKey('users.User', on_delete=models.CASCADE)  # String reference
    
    def __str__(self):
        return f"Receipt {self.receipt_number} - {self.amount_paid}"