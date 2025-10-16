from django import template

register = template.Library()

@register.filter
def is_school_admin(user):
    return user.user_type in ['senior_admin', 'junior_admin']

@register.filter
def is_teacher(user):
    return user.user_type == 'teacher'

@register.filter
def is_student(user):
    return user.user_type == 'student'

@register.filter
def is_super_admin(user):
    return user.user_type == 'super_admin'
