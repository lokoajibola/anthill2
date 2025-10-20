from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User
from users.models import School
from schools.models import SchoolAdmin
from academic.models import Subject
from django.core.exceptions import ValidationError


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
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter password'
        }),
        min_length=8,
        help_text="Password must be at least 8 characters long."
    )
    confirm_password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control', 
            'placeholder': 'Confirm password'
        })
    )
    guardian_phone = forms.CharField(max_length=15, required=False, label="Parent/Guardian Phone")
    address = forms.CharField(widget=forms.Textarea(attrs={'rows': 3}), required=False)
    
    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'phone', 'profile_picture', 'city', 'lga', 'address', 'password', 'confirm_password', 'guardian_phone']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'profile_picture': forms.FileInput(attrs={'class': 'form-control'}),
        }
    
    def __init__(self, *args, **kwargs):
        self.user_type = kwargs.pop('user_type', 'teacher')
        self.school = kwargs.pop('school', None)
        super().__init__(*args, **kwargs)
        
        # Make email required for certain user types
        if self.user_type in ['teacher', 'senior_admin', 'junior_admin']:
            self.fields['email'].required = True
        
        # Add help text for username
        self.fields['username'].help_text = f"Username must be unique within {self.school.name if self.school else 'the school'}."
    
    def clean_username(self):
        username = self.cleaned_data['username']
        
        if self.school:
            # Check if username already exists in this school
            if User.objects.filter(username=username, school=self.school).exists():
                raise ValidationError(f'Username "{username}" is already taken in {self.school.name}.')
        
        return username
    
    def clean_email(self):
        email = self.cleaned_data['email']
        
        if email and self.school:
            # Check if email already exists in this school (optional)
            if User.objects.filter(email=email, school=self.school).exists():
                raise ValidationError(f'Email "{email}" is already registered in {self.school.name}.')
        
        return email
    
    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        confirm_password = cleaned_data.get('confirm_password')
        
        if password and confirm_password and password != confirm_password:
            self.add_error('confirm_password', "Passwords do not match.")
        
        return cleaned_data
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.user_type = self.user_type
        user.school = self.school
        user.set_password(self.cleaned_data['password'])
        
        if commit:
            try:
                user.save()
                
                if self.user_type == 'teacher':
                    from users.models import Teacher
                    Teacher.objects.get_or_create(user=user, school=self.school)
                    
                elif self.user_type == 'student':
                    from users.models import Student
                    # Generate admission number without school code
                    last_student = Student.objects.filter(school=self.school).order_by('-id').first()
                    next_id = last_student.id + 1 if last_student else 1
                    admission_number = f"STD{next_id:06d}"
                    
                    student = Student.objects.create(
                        user=user, 
                        school=self.school,
                        admission_number=admission_number
                    )
                    # Save guardian phone if provided
                    if self.cleaned_data.get('guardian_phone'):
                        student.guardian_phone = self.cleaned_data['guardian_phone']
                        student.save()
                    
                elif self.user_type == 'junior_admin':
                    SchoolAdmin.objects.get_or_create(
                        user=user, 
                        school=self.school,
                        defaults={'is_senior': False}
                    )
                
                elif self.user_type == 'senior_admin':
                    SchoolAdmin.objects.get_or_create(
                        user=user, 
                        school=self.school, 
                        defaults={'is_senior': True}
                    )
                    
            except Exception as e:
                if user.pk:
                    user.delete()
                raise ValidationError(f"Error creating user profile: {str(e)}")
        
        return user
    
class SubjectForm(forms.ModelForm):
    class Meta:
        model = Subject
        fields = ['name', 'code', 'description']
    
    def __init__(self, *args, **kwargs):
        self.school = kwargs.pop('school', None)
        super().__init__(*args, **kwargs)
    
    def save(self, commit=True):
        subject = super().save(commit=False)
        subject.school = self.school
        if commit:
            subject.save()
        return subject