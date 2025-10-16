from django.db import models
from users.models import User
from django.utils import timezone


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
    logo = models.ImageField(upload_to='schools/logos/')
    motto = models.CharField(max_length=300, blank=True)
    vision = models.TextField(blank=True)
    mission = models.TextField(blank=True)
    primary_color = models.CharField(max_length=7, default='#000000')
    school_type = models.CharField(max_length=20, choices=SCHOOL_TYPES)
    subscription_type = models.CharField(max_length=20, choices=SUBSCRIPTION_TYPES)
    phone = models.CharField(max_length=15)
    email = models.EmailField()
    address = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.name

class SchoolAdmin(models.Model):
    school = models.ForeignKey(School, on_delete=models.CASCADE)
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    is_senior = models.BooleanField(default=False)
    
    class Meta:
        unique_together = ['school', 'is_senior']


class Payment(models.Model):
    PAYMENT_STATUS = (
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded'),
    )
    
    school = models.ForeignKey(School, on_delete=models.CASCADE)
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

class Subscription(models.Model):
    school = models.OneToOneField(School, on_delete=models.CASCADE)
    start_date = models.DateField()
    end_date = models.DateField()
    is_active = models.BooleanField(default=True)
    auto_renew = models.BooleanField(default=True)
    
    def is_expired(self):
        return timezone.now().date() > self.end_date
    
    def days_remaining(self):
        return (self.end_date - timezone.now().date()).days
    
    def __str__(self):
        return f"{self.school.name} - {self.school.get_subscription_type_display()}"