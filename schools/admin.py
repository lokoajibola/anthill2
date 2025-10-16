from django.contrib import admin
from .models import School, SchoolAdmin, Payment, Subscription

@admin.register(School)
class SchoolAdminModel(admin.ModelAdmin):  # Changed from SchoolAdmin
    list_display = ['name', 'school_type', 'subscription_type', 'email', 'phone']
    list_filter = ['school_type', 'subscription_type']
    search_fields = ['name', 'email']

@admin.register(SchoolAdmin)
class SchoolAdminRelationAdmin(admin.ModelAdmin):  # Changed from SchoolAdminAdmin
    list_display = ['school', 'user', 'is_senior']
    list_filter = ['is_senior', 'school']

@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ['school', 'start_date', 'end_date', 'is_active']
    list_filter = ['is_active']

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ['school', 'amount', 'payment_date', 'status']
    list_filter = ['status']