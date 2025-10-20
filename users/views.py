from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.contrib import messages
from .forms import SchoolRegistrationForm
from .models import User, Teacher, Student
from schools.models import SchoolAdmin, School
from django.contrib.auth.backends import ModelBackend



# users/views.py
def custom_login(request):
    schools = School.objects.filter(is_active=True)
    
    if request.method == 'POST':
        school_id = request.POST.get('school')
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        # Handle super admin login (no school selected)
        if not school_id:
            user = authenticate(request, username=username, password=password)
            if user and user.user_type == 'super_admin':
                login(request, user)
                return redirect('admin:index')
            else:
                messages.error(request, 'Invalid credentials for super admin access.')
                return render(request, 'users/login.html', {'schools': schools})
        
        # Handle school user login
        try:
            school = School.objects.get(id=school_id, is_active=True)
            user = authenticate(request, username=username, password=password, school=school)
            
            if user is not None:
                login(request, user)
                # Redirect based on user type
                if user.user_type == 'super_admin':
                    return redirect('admin:index')
                elif user.is_school_admin:
                    return redirect('schools:dashboard')
                elif user.user_type == 'teacher':
                    return redirect('academic:teacher_dashboard')
                elif user.user_type == 'student':
                    return redirect('academic:student_dashboard')
            else:
                messages.error(request, 'Invalid username, password, or school.')
                
        except School.DoesNotExist:
            messages.error(request, 'Invalid school selected.')
    
    return render(request, 'users/login.html', {'schools': schools})

def register_school(request):
    if request.method == 'POST':
        print("POST request received for registration")
        form = SchoolRegistrationForm(request.POST, request.FILES)
        print("Form data:", request.POST)
        
        if form.is_valid():
            print("Form is valid, creating user and school...")
            try:
                user = form.save()
                print(f"User created: {user.username} with type: {user.user_type}")
                
                # Move login inside the try block
                login(request, user, backend='django.contrib.auth.backends.ModelBackend')
                messages.success(request, 'School registered successfully!')
                print("Redirecting to schools dashboard...")
                return redirect('schools:dashboard')
                
            except Exception as e:
                print(f"Error during registration: {str(e)}")
                messages.error(request, f'Error during registration: {str(e)}')
        else:
            print("Form errors:", form.errors)
            messages.error(request, 'Please correct the errors below.')
    else:
        form = SchoolRegistrationForm()
    
    return render(request, 'users/register.html', {'form': form})

def user_login(request):
    # If user is already authenticated, redirect them immediately
    if request.user.is_authenticated:
        print(f"User already authenticated: {request.user.username}, redirecting...")
        return redirect_user_by_type(request.user)
    
    if request.method == 'POST':
        print("Login POST received")
        print("POST data:", request.POST)
        
        # Use the standard AuthenticationForm
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            print("Login form is valid")
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            print(f"Attempting to authenticate user: {username}")
            
            user = authenticate(username=username, password=password)
            if user is not None:
                print(f"User authenticated successfully: {user.username}")
                print(f"User type: {user.user_type}")
                print(f"User is_active: {user.is_active}")
                
                # Log the user in
                login(request, user)
                messages.success(request, f'Welcome back, {user.username}!')
                print("Login successful, redirecting...")
                
                # Redirect based on user type
                return redirect_user_by_type(user)
            else:
                print("Authentication failed - user is None")
                messages.error(request, 'Invalid username or password.')
        else:
            print("Login form errors:", form.errors)
            messages.error(request, 'Invalid username or password.')
    else:
        form = AuthenticationForm()
    
    return render(request, 'users/login.html', {'form': form})

def redirect_user_by_type(user):
    """Helper function to redirect users based on their type"""
    print(f"=== REDIRECT LOGIC ===")
    print(f"User: {user.username}")
    print(f"User type: {user.user_type}")
    print(f"Is authenticated: {user.is_authenticated}")
    
    if user.user_type == 'super_admin':
        print("Redirecting to ADMIN index")
        return redirect('admin:index')
    elif user.user_type in ['senior_admin', 'junior_admin']:
        print("Redirecting to SCHOOLS dashboard")
        return redirect('schools:dashboard')
    elif user.user_type == 'teacher':
        print("Redirecting to TEACHER dashboard")
        return redirect('users:teacher_dashboard')
    elif user.user_type == 'student':
        print("Redirecting to STUDENT dashboard")
        return redirect('users:student_dashboard')
    else:
        print("Unknown user type, redirecting to homepage")
        return redirect('homepage')

def user_logout(request):
    logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('users:login')

@login_required
def teacher_dashboard(request):
    if request.user.user_type != 'teacher':
        messages.error(request, 'You do not have permission to access this page.')
        return redirect_user_by_type(request.user)
    
    try:
        teacher = Teacher.objects.get(user=request.user)
        context = {
            'teacher': teacher,
            'school': teacher.school,
        }
        return render(request, 'users/teacher_dashboard.html', context)
    except Teacher.DoesNotExist:
        messages.error(request, 'Teacher profile not found.')
        return redirect('homepage')

@login_required
def student_dashboard(request):
    if request.user.user_type != 'student':
        messages.error(request, 'You do not have permission to access this page.')
        return redirect_user_by_type(request.user)
    
    try:
        student = Student.objects.get(user=request.user)
        context = {
            'student': student,
            'school': student.school,
        }
        return render(request, 'users/student_dashboard.html', context)
    except Student.DoesNotExist:
        messages.error(request, 'Student profile not found.')
        return redirect('homepage')
    
@login_required
def edit_profile(request):
    user = request.user
    
    if request.method == 'POST':
        user.first_name = request.POST.get('first_name', user.first_name)
        user.last_name = request.POST.get('last_name', user.last_name)
        user.email = request.POST.get('email', user.email)
        user.phone = request.POST.get('phone', user.phone)
        
        if 'profile_picture' in request.FILES:
            user.profile_picture = request.FILES['profile_picture']
        
        # Handle student-specific fields
        if user.user_type == 'student':
            student = Student.objects.get(user=user)
            if request.POST.get('admission_number'):
                student.admission_number = request.POST.get('admission_number')
            student.save()
        
        user.save()
        messages.success(request, 'Profile updated successfully!')
        return redirect('users:edit_profile')
    
    context = {'user': user}
    if user.user_type == 'student':
        context['student'] = Student.objects.get(user=user)
    
    return render(request, 'users/edit_profile.html', context)