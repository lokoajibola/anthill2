# users/backends.py
from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model
from schools.models import School

User = get_user_model()

class SchoolSpecificAuthBackend(ModelBackend):
    def authenticate(self, request, username=None, password=None, school=None, **kwargs):
        try:
            if school:
                # Check if user exists with this username in the specific school
                user = User.objects.get(
                    username=username,
                    school=school  # Assuming User model has a school field
                )
            else:
                # Fallback to global lookup (for superusers, etc.)
                user = User.objects.get(username=username)
            
            if user.check_password(password):
                return user
        except User.DoesNotExist:
            return None
    
    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None
        
# users/backends.py
class SchoolSpecificAuthBackend(ModelBackend):
    def authenticate(self, request, username=None, password=None, school=None, **kwargs):
        try:
            # For super admins (no school needed)
            if not school:
                user = User.objects.get(username=username, school__isnull=True)
                if user.check_password(password) and user.user_type == 'super_admin':
                    return user
                return None
            
            # For school users
            school_obj = School.objects.get(id=school, is_active=True)
            user = User.objects.get(username=username, school=school_obj)
            
            if user.check_password(password):
                return user
                
        except (User.DoesNotExist, School.DoesNotExist):
            return None