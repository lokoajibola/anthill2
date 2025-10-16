from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User
from schools.models import School, SchoolAdmin

class SchoolRegistrationForm(UserCreationForm):
    # School fields
    school_name = forms.CharField(max_length=200, required=True)
    school_logo = forms.ImageField(required=False)
    school_motto = forms.CharField(max_length=300, required=False)
    school_vision = forms.CharField(widget=forms.Textarea, required=False)
    school_mission = forms.CharField(widget=forms.Textarea, required=False)
    school_primary_color = forms.CharField(max_length=7, initial='#000000')
    school_type = forms.ChoiceField(choices=School.SCHOOL_TYPES)
    subscription_type = forms.ChoiceField(choices=School.SUBSCRIPTION_TYPES)
    school_phone = forms.CharField(max_length=15, required=True)
    school_email = forms.EmailField(required=True)
    school_address = forms.CharField(widget=forms.Textarea, required=True)
    
    # Note: Using the same field names as the User model
    # first_name, last_name, email, phone are already in UserCreationForm

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'phone', 'password1', 'password2']

    def clean(self):
        cleaned_data = super().clean()
        # Check if username already exists
        if User.objects.filter(username=cleaned_data.get('username')).exists():
            raise forms.ValidationError("Username already exists. Please choose a different one.")
        return cleaned_data

    def save(self, commit=True):
        # Create the user first
        user = super().save(commit=False)
        user.user_type = 'senior_admin'
        # first_name, last_name, email, phone are already set by the parent form
        
        if commit:
            user.save()
            print(f"User created: {user.username} with type: {user.user_type}")
            
            # Create the school
            school = School.objects.create(
                name=self.cleaned_data['school_name'],
                motto=self.cleaned_data['school_motto'],
                vision=self.cleaned_data['school_vision'],
                mission=self.cleaned_data['school_mission'],
                primary_color=self.cleaned_data['school_primary_color'],
                school_type=self.cleaned_data['school_type'],
                subscription_type=self.cleaned_data['subscription_type'],
                phone=self.cleaned_data['school_phone'],
                email=self.cleaned_data['school_email'],
                address=self.cleaned_data['school_address'],
            )
            
            if self.cleaned_data.get('school_logo'):
                school.logo = self.cleaned_data['school_logo']
                school.save()
            
            # Create school admin relationship
            SchoolAdmin.objects.create(
                school=school,
                user=user,
                is_senior=True
            )
            print(f"School created: {school.name}")
        
        return user

class CreateUserForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput)
    
    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'phone', 'profile_picture']
    
    def __init__(self, *args, **kwargs):
        self.user_type = kwargs.pop('user_type', 'teacher')
        self.school = kwargs.pop('school', None)
        super().__init__(*args, **kwargs)
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.user_type = self.user_type
        user.set_password(self.cleaned_data['password'])
        
        if commit:
            user.save()
            
            if self.user_type == 'teacher':
                from .models import Teacher
                Teacher.objects.create(user=user, school=self.school)
            elif self.user_type == 'student':
                from .models import Student
                Student.objects.create(user=user, school=self.school, admission_number=f"STD{user.id:06d}")
            elif self.user_type == 'junior_admin':
                SchoolAdmin.objects.create(user=user, school=self.school, is_senior=False)
        
        return user