from django.shortcuts import render, get_object_or_404
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .models import School, SchoolAdmin, Payment, Subscription, StudentFee
from django.contrib import messages
from django.db.models import Q, Count
from users.models import User, Teacher, Student
from users.forms import CreateUserForm
from django.utils import timezone  # Add timezone import
from academic.models import ClassLevel, Assignment, FeeStructure, Subject, ClassSubject
# from .schools.model import StudentFee
from django.contrib.auth import logout
from users.forms import SubjectForm


@login_required
def edit_school_homepage(request):
    school_admin = get_object_or_404(SchoolAdmin, user=request.user)
    school = school_admin.school
    
    if request.method == 'POST':
        print("Updating school information...")
        
        # Update school information
        school.name = request.POST.get('name', school.name)
        school.motto = request.POST.get('motto', school.motto)
        school.vision = request.POST.get('vision', school.vision)
        school.mission = request.POST.get('mission', school.mission)
        school.primary_color = request.POST.get('primary_color', school.primary_color)
        school.phone = request.POST.get('phone', school.phone)
        school.email = request.POST.get('email', school.email)
        school.address = request.POST.get('address', school.address)
        
        if 'logo' in request.FILES:
            school.logo = request.FILES['logo']
        
        school.save()
        messages.success(request, 'School information updated successfully!')
        return redirect('schools:edit_homepage')
    
    return render(request, 'schools/edit_homepage.html', {
        'school': school,
        'is_senior_admin': school_admin.is_senior
    })

def school_homepage(request, school_id):
    school = get_object_or_404(School, id=school_id)
    
    return render(request, 'schools/school_homepage.html', {
        'school': school
    })


@login_required
def search_entities(request):
    query = request.GET.get('q', '')
    results = {}
    
    if query:
        # Search across schools, teachers, and students
        schools = School.objects.filter(
            Q(name__icontains=query) | 
            Q(email__icontains=query)
        )
        
        teachers = User.objects.filter(
            Q(user_type='teacher') &
            (Q(username__icontains=query) | 
             Q(first_name__icontains=query) | 
             Q(last_name__icontains=query))
        )
        
        students = User.objects.filter(
            Q(user_type='student') &
            (Q(username__icontains=query) | 
             Q(first_name__icontains=query) | 
             Q(last_name__icontains=query))
        )
        
        results = {
            'schools': schools,
            'teachers': teachers,
            'students': students,
        }
    
    return render(request, 'schools/search.html', {
        'results': results,
        'query': query
    })

@login_required
def manage_gallery(request):
    school_admin = get_object_or_404(SchoolAdmin, user=request.user)
    school = school_admin.school
    images = GalleryImage.objects.filter(school=school)
    
    if request.method == 'POST':
        image = request.FILES.get('image')
        title = request.POST.get('title')
        description = request.POST.get('description')
        
        GalleryImage.objects.create(
            school=school,
            image=image,
            title=title,
            description=description
        )
        messages.success(request, 'Image added to gallery!')
        return redirect('schools:manage_gallery')
    
    return render(request, 'schools/manage_gallery.html', {
        'school': school,
        'images': images
    })

@login_required  
def delete_gallery_image(request, image_id):
    school_admin = get_object_or_404(SchoolAdmin, user=request.user)
    image = get_object_or_404(GalleryImage, id=image_id, school=school_admin.school)
    image.delete()
    messages.success(request, 'Image deleted!')
    return redirect('schools:manage_gallery')

@login_required
def manage_admission(request):
    school_admin = get_object_or_404(SchoolAdmin, user=request.user)
    school = school_admin.school
    
    try:
        admission_info = AdmissionInfo.objects.get(school=school)
    except AdmissionInfo.DoesNotExist:
        admission_info = None
    
    if request.method == 'POST':
        requirements = request.POST.get('requirements')
        process = request.POST.get('process')
        fees = request.POST.get('fees')
        contact_info = request.POST.get('contact_info')
        
        if admission_info:
            admission_info.requirements = requirements
            admission_info.process = process
            admission_info.fees = fees
            admission_info.contact_info = contact_info
            admission_info.save()
        else:
            admission_info = AdmissionInfo.objects.create(
                school=school,
                requirements=requirements,
                process=process,
                fees=fees,
                contact_info=contact_info
            )
        
        messages.success(request, 'Admission information updated!')
        return redirect('schools:manage_admission')
    
    return render(request, 'schools/manage_admission.html', {
        'school': school,
        'admission_info': admission_info
    })

@login_required
def create_user(request, user_type):
    school_admin = get_object_or_404(SchoolAdmin, user=request.user)
    
    if not school_admin.is_senior:
        messages.error(request, "Only senior admins can create users.")
        return redirect('schools:dashboard')
    
    if request.method == 'POST':
        form = CreateUserForm(request.POST, request.FILES, user_type=user_type, school=school_admin.school)
        if form.is_valid():
            try:
                user = form.save()
                
                if user_type == 'student':
                    from users.models import Student
                    class_level_id = request.POST.get('class_level')
                    if class_level_id:
                        class_level = ClassLevel.objects.get(id=class_level_id, school=school_admin.school)
                        student = Student.objects.get(user=user)
                        student.guardian_phone = form.cleaned_data.get('guardian_phone', '')
                        student.class_level = class_level
                        student.save()
                        
                        compulsory_subjects = ClassSubject.objects.filter(
                            class_level=class_level, 
                            is_compulsory=True
                        )
                        for cs in compulsory_subjects:
                            student.elective_subjects.add(cs.subject)
                
                messages.success(request, f'{user_type.title()} created successfully!')
                return redirect('schools:manage_users')
            
            except Exception as e:
                # Print detailed error for debugging
                import traceback
                print("Error creating user:", str(e))
                print("Traceback:", traceback.format_exc())
                messages.error(request, f'Error creating user: {str(e)}')
        else:
            # Print form errors to console
            print("Form errors:", form.errors.as_json())
            messages.error(request, 'Please correct the errors below.')
    else:
        form = CreateUserForm(user_type=user_type, school=school_admin.school)
    
    class_levels = ClassLevel.objects.filter(school=school_admin.school)
    
    return render(request, 'schools/create_user.html', {
        'form': form,
        'user_type': user_type,
        'school': school_admin.school,
        'class_levels': class_levels,
    })

@login_required
def manage_classes(request):
    school_admin = get_object_or_404(SchoolAdmin, user=request.user)
    school = school_admin.school
    classes = ClassLevel.objects.filter(school=school)
    
    return render(request, 'schools/manage_classes.html', {
        'school': school,
        'classes': classes
    })

@login_required
def create_class(request):
    school_admin = get_object_or_404(SchoolAdmin, user=request.user)
    school = school_admin.school
    
    if request.method == 'POST':
        name = request.POST.get('name')
        level = request.POST.get('level')
        
        ClassLevel.objects.create(
            name=name,
            level=level,
            school=school
        )
        messages.success(request, 'Class created successfully!')
        return redirect('schools:manage_classes')
    
    return render(request, 'schools/create_class.html', {
        'school': school
    })

@login_required
def manage_fees(request):
    school_admin = get_object_or_404(SchoolAdmin, user=request.user)
    school = school_admin.school
    
    fee_structures = FeeStructure.objects.filter(school=school, is_active=True)
    class_levels = ClassLevel.objects.filter(school=school)
    
    if request.method == 'POST':
        if 'create_fee' in request.POST:
            name = request.POST.get('name')
            fee_type = request.POST.get('fee_type')
            amount = request.POST.get('amount')
            applicable_to = request.POST.get('applicable_to')
            class_level_id = request.POST.get('class_level')
            due_date = request.POST.get('due_date')
            
            fee_structure = FeeStructure.objects.create(
                school=school,
                name=name,
                fee_type=fee_type,
                amount=amount,
                applicable_to=applicable_to,
                due_date=due_date
            )
            
            if applicable_to == 'class' and class_level_id:
                fee_structure.class_level_id = class_level_id
                fee_structure.save()
            
            messages.success(request, 'Fee structure created!')
            return redirect('schools:manage_fees')
    
    return render(request, 'schools/manage_fees.html', {
        'school': school,
        'fee_structures': fee_structures,
        'class_levels': class_levels
    })

@login_required
def create_subject(request):
    school_admin = get_object_or_404(SchoolAdmin, user=request.user)
    
    if request.method == 'POST':
        form = SubjectForm(request.POST, school=school_admin.school)
        if form.is_valid():
            subject = form.save()
            # form = SubjectForm(school=school_admin.school)
            messages.success(request, f'Subject "{subject.name}" created successfully!')
            return redirect('schools:create_subject')
            form = SubjectForm(school=school_admin.school)  # Reset form for new entry
    else:
        form = SubjectForm(school=school_admin.school)
    
    return render(request, 'schools/create_subject.html', {'form': form})

@login_required
def student_fee_search(request):
    school_admin = get_object_or_404(SchoolAdmin, user=request.user)
    school = school_admin.school
    
    students = Student.objects.filter(school=school)
    query = request.GET.get('q', '')
    
    if query:
        students = students.filter(
            Q(user__first_name__icontains=query) |
            Q(user__last_name__icontains=query) |
            Q(admission_number__icontains=query)
        )
    
    return render(request, 'schools/student_fee_search.html', {
        'school': school,
        'students': students,
        'query': query
    })

@login_required
def student_fee_details(request, student_id):
    school_admin = get_object_or_404(SchoolAdmin, user=request.user)
    student = get_object_or_404(Student, id=student_id, school=school_admin.school)
    
    student_fees = StudentFee.objects.filter(student=student).select_related('fee_structure')
    
    if request.method == 'POST':
        if 'mark_paid' in request.POST:
            student_fee_id = request.POST.get('student_fee_id')
            student_fee = get_object_or_404(StudentFee, id=student_fee_id, student=student)
            
            # Create payment record
            receipt_number = f"RCP{student_fee.id}{timezone.now().strftime('%Y%m%d%H%M%S')}"
            FeePayment.objects.create(
                student_fee=student_fee,
                amount_paid=student_fee.balance(),
                receipt_number=receipt_number,
                recorded_by=request.user
            )
            
            # Update student fee
            student_fee.amount_paid = student_fee.amount_due
            student_fee.payment_status = 'paid'
            student_fee.save()
            
            messages.success(request, f'Fee marked as fully paid! Receipt: {receipt_number}')
        
        elif 'add_payment' in request.POST:
            student_fee_id = request.POST.get('student_fee_id')
            amount_paid = request.POST.get('amount_paid')
            payment_method = request.POST.get('payment_method')
            
            student_fee = get_object_or_404(StudentFee, id=student_fee_id, student=student)
            
            # Create payment record
            receipt_number = f"RCP{student_fee.id}{timezone.now().strftime('%Y%m%d%H%M%S')}"
            FeePayment.objects.create(
                student_fee=student_fee,
                amount_paid=amount_paid,
                payment_method=payment_method,
                receipt_number=receipt_number,
                recorded_by=request.user
            )
            
            # Update student fee
            student_fee.amount_paid += Decimal(amount_paid)
            if student_fee.amount_paid >= student_fee.amount_due:
                student_fee.payment_status = 'paid'
            elif student_fee.amount_paid > 0:
                student_fee.payment_status = 'partial'
            student_fee.save()
            
            messages.success(request, f'Payment recorded! Receipt: {receipt_number}')
    
    # Calculate totals
    total_due = sum(fee.amount_due for fee in student_fees)
    total_paid = sum(fee.amount_paid for fee in student_fees)
    total_balance = total_due - total_paid
    
    return render(request, 'schools/student_fee_details.html', {
        'school': school_admin.school,
        'student': student,
        'student_fees': student_fees,
        'total_due': total_due,
        'total_paid': total_paid,
        'total_balance': total_balance
    })

@login_required
def fee_analytics(request):
    school_admin = get_object_or_404(SchoolAdmin, user=request.user)
    school = school_admin.school
    
    # Fee summary
    total_fees_due = StudentFee.objects.filter(student__school=school).aggregate(
        total_due=models.Sum('amount_due'),
        total_paid=models.Sum('amount_paid')
    )
    
    # Payment status distribution
    status_distribution = StudentFee.objects.filter(student__school=school).values(
        'payment_status'
    ).annotate(
        count=models.Count('id'),
        amount=models.Sum('amount_due')
    )
    
    # Fee type distribution
    fee_type_distribution = FeeStructure.objects.filter(school=school).values(
        'fee_type'
    ).annotate(
        total_amount=models.Sum('amount'),
        count=models.Count('id')
    )
    
    # Recent payments
    recent_payments = FeePayment.objects.filter(
        student_fee__student__school=school
    ).select_related('student_fee__student__user', 'recorded_by').order_by('-payment_date')[:10]
    
    return render(request, 'schools/fee_analytics.html', {
        'school': school,
        'total_fees_due': total_fees_due,
        'status_distribution': status_distribution,
        'fee_type_distribution': fee_type_distribution,
        'recent_payments': recent_payments
    })


@login_required
def class_subjects(request, class_id):
    school_admin = get_object_or_404(SchoolAdmin, user=request.user)
    class_level = get_object_or_404(ClassLevel, id=class_id, school=school_admin.school)
    
    if request.method == 'POST':
        # Clear existing subjects
        if 'clear_all' in request.POST:
            ClassSubject.objects.filter(class_level=class_level).delete()
            messages.success(request, 'All subjects cleared from class!')
            return redirect('schools:class_subjects', class_id=class_id)
        
        # Delete specific subject
        if 'delete_subject' in request.POST:
            subject_id = request.POST.get('delete_subject')
            ClassSubject.objects.filter(id=subject_id, class_level=class_level).delete()
            messages.success(request, 'Subject removed from class!')
            return redirect('schools:class_subjects', class_id=class_id)
        
        # Add subjects to class AND assign to teacher
        subject_id = request.POST.get('subject')
        is_compulsory = request.POST.get('is_compulsory') == 'on'
        teacher_id = request.POST.get('teacher')
        
        if subject_id and teacher_id:
            subject = Subject.objects.get(id=subject_id)
            teacher = Teacher.objects.get(id=teacher_id, school=school_admin.school)
            
            # 1. Add to ClassSubject (for class-subject relationship)
            ClassSubject.objects.update_or_create(
                class_level=class_level,
                subject=subject,
                defaults={
                    'is_compulsory': is_compulsory,
                    'teacher': teacher
                }
            )
            
            # 2. ALSO add to teacher's direct subjects (for teacher dashboard)
            teacher.subjects.add(subject)
            
            messages.success(request, f'{subject.name} assigned to {teacher.user.get_full_name()}!')
            return redirect('schools:class_subjects', class_id=class_id)
        else:
            messages.error(request, 'Please select both subject and teacher.')
    
    class_subjects = ClassSubject.objects.filter(class_level=class_level).select_related('subject', 'teacher', 'teacher__user')
    available_subjects = Subject.objects.all()
    teachers = Teacher.objects.filter(school=school_admin.school).select_related('user')
    
    return render(request, 'schools/class_subjects.html', {
        'school': school_admin.school,
        'class_level': class_level,
        'class_subjects': class_subjects,
        'available_subjects': available_subjects,
        'teachers': teachers
    })


@login_required
def manage_class_students(request, class_id):
    school_admin = get_object_or_404(SchoolAdmin, user=request.user)
    class_level = get_object_or_404(ClassLevel, id=class_id, school=school_admin.school)
    
    if request.method == 'POST':
        if 'search_student' in request.POST:
            query = request.POST.get('query')
            students = Student.objects.filter(
                school=school_admin.school,
                admission_number__icontains=query
            ).exclude(class_level=class_level)
        elif 'add_student' in request.POST:
            student_id = request.POST.get('student_id')
            student = Student.objects.get(id=student_id, school=school_admin.school)
            student.class_level = class_level
            student.save()
            messages.success(request, f'{student.user.get_full_name()} added to class!')
        elif 'remove_student' in request.POST:
            student_id = request.POST.get('student_id')
            student = Student.objects.get(id=student_id, school=school_admin.school)
            student.class_level = None
            student.save()
            messages.success(request, f'{student.user.get_full_name()} removed from class!')
    
    class_students = Student.objects.filter(class_level=class_level)
    all_students = Student.objects.filter(school=school_admin.school, class_level__isnull=True)
    
    return render(request, 'schools/manage_class_students.html', {
        'school': school_admin.school,
        'class_level': class_level,
        'class_students': class_students,
        'all_students': all_students
    })


@login_required
def school_dashboard(request):
    print(f"=== SCHOOL DASHBOARD ACCESSED ===")
    print(f"User: {request.user.username}")
    print(f"User type: {request.user.user_type}")
    
    # Check if user is a school admin
    if request.user.user_type not in ['senior_admin', 'junior_admin']:
        messages.error(request, 'You do not have permission to access the school dashboard.')
        return redirect('homepage')
    
    try:
        school_admin = SchoolAdmin.objects.get(user=request.user)
        school = school_admin.school
        
        # Get counts for dashboard
        teachers_count = Teacher.objects.filter(school=school).count()
        students_count = Student.objects.filter(school=school).count()
        junior_admins_count = SchoolAdmin.objects.filter(school=school, is_senior=False).count()
        
        context = {
            'school': school,
            'is_senior_admin': school_admin.is_senior,
            'teachers_count': teachers_count,
            'students_count': students_count,
            'junior_admins_count': junior_admins_count,
        }
        
        print(f"Rendering dashboard for school: {school.name}")
        return render(request, 'schools/dashboard.html', context)
        
    except SchoolAdmin.DoesNotExist:
        print("SchoolAdmin relationship not found for user")
        messages.error(request, 'School administrator profile not found.')
        return redirect('homepage')
    except Exception as e:
        print(f"Error in school_dashboard: {str(e)}")
        messages.error(request, 'An error occurred while accessing the dashboard.')
        return redirect('homepage')

@login_required
def manage_users(request):
    school_admin = get_object_or_404(SchoolAdmin, user=request.user)
    
    if not school_admin.is_senior:
        return redirect('schools:dashboard')
    
    school = school_admin.school
    teachers = User.objects.filter(teacher__school=school) if hasattr(User, 'teacher') else []
    students = User.objects.filter(student__school=school) if hasattr(User, 'student') else []
    junior_admins = SchoolAdmin.objects.filter(school=school, is_senior=False)
    
    context = {
        'school': school,
        'teachers': teachers,
        'students': students,
        'junior_admins': junior_admins,
    }
    return render(request, 'schools/manage_users.html', context)

@login_required
def edit_school_homepage(request):
    school_admin = get_object_or_404(SchoolAdmin, user=request.user)
    school = school_admin.school
    
    if request.method == 'POST':
        # Handle school info update
        school.motto = request.POST.get('motto', school.motto)
        school.vision = request.POST.get('vision', school.vision)
        school.mission = request.POST.get('mission', school.mission)
        school.primary_color = request.POST.get('primary_color', school.primary_color)
        
        if 'logo' in request.FILES:
            school.logo = request.FILES['logo']
        
        school.save()
        messages.success(request, 'School information updated successfully!')
        return redirect('schools:edit_homepage')
    
    return render(request, 'schools/edit_homepage.html', {
        'school': school
    })

@login_required
def search_entities(request):
    query = request.GET.get('q', '')
    results = {}
    
    if query:
        # Search schools (for super admin)
        if request.user.user_type == 'super_admin':
            schools = School.objects.filter(
                Q(name__icontains=query) | 
                Q(email__icontains=query) |
                Q(phone__icontains=query)
            )
            results['schools'] = schools
        
        # Search teachers and students within the school
        school_admin = get_object_or_404(SchoolAdmin, user=request.user)
        school = school_admin.school
        
        teachers = User.objects.filter(
            Q(user_type='teacher') &
            Q(teacher__school=school) &
            (Q(username__icontains=query) | 
             Q(first_name__icontains=query) | 
             Q(last_name__icontains=query) |
             Q(email__icontains=query))
        )
        
        students = User.objects.filter(
            Q(user_type='student') &
            Q(student__school=school) &
            (Q(username__icontains=query) | 
             Q(first_name__icontains=query) | 
             Q(last_name__icontains=query) |
             Q(email__icontains=query) |
             Q(student__admission_number__icontains=query))
        )
        
        results.update({
            'teachers': teachers,
            'students': students,
        })
    
    return render(request, 'schools/search.html', {
        'results': results,
        'query': query,
        'school': getattr(SchoolAdmin.objects.filter(user=request.user).first(), 'school', None)
    })

@login_required
def edit_user(request, user_id):
    school_admin = get_object_or_404(SchoolAdmin, user=request.user)
    
    if not school_admin.is_senior:
        messages.error(request, "Only senior admins can edit users.")
        return redirect('schools:dashboard')
    
    user = get_object_or_404(User, id=user_id)
    
    # Ensure user belongs to the same school
    if user.user_type == 'teacher':
        teacher = get_object_or_404(Teacher, user=user, school=school_admin.school)
    elif user.user_type == 'student':
        student = get_object_or_404(Student, user=user, school=school_admin.school)
    elif user.user_type == 'junior_admin':
        junior_admin = get_object_or_404(SchoolAdmin, user=user, school=school_admin.school)
    
    if request.method == 'POST':
        user.first_name = request.POST.get('first_name', user.first_name)
        user.last_name = request.POST.get('last_name', user.last_name)
        user.email = request.POST.get('email', user.email)
        user.phone = request.POST.get('phone', user.phone)
        
        if 'profile_picture' in request.FILES:
            user.profile_picture = request.FILES['profile_picture']
        
        user.save()
        
        # Update student-specific fields
        if user.user_type == 'student':
            student.admission_number = request.POST.get('admission_number', student.admission_number)
            if request.POST.get('class_level'):
                student.class_level_id = request.POST.get('class_level')
            student.save()
        
        messages.success(request, f'{user.get_full_name()} updated successfully!')
        return redirect('schools:manage_users')
    
    class_levels = ClassLevel.objects.filter(school=school_admin.school)
    
    return render(request, 'schools/edit_user.html', {
        'user': user,
        'school': school_admin.school,
        'class_levels': class_levels,
    })

@login_required
def delete_user(request, user_id):
    school_admin = get_object_or_404(SchoolAdmin, user=request.user)
    
    if not school_admin.is_senior:
        messages.error(request, "Only senior admins can delete users.")
        return redirect('schools:dashboard')
    
    user = get_object_or_404(User, id=user_id)
    
    # Ensure user belongs to the same school and is not the current user
    if user == request.user:
        messages.error(request, "You cannot delete your own account.")
        return redirect('schools:manage_users')
    
    user_name = user.get_full_name()
    user_type = user.user_type
    
    # Delete the user (this will cascade to related records)
    user.delete()
    
    messages.success(request, f'{user_type.title()} {user_name} deleted successfully!')
    return redirect('schools:manage_users')

def user_logout(request):
    logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('homepage')

@login_required
def admin_analytics(request):
    """Super admin analytics across all schools"""
    if request.user.user_type != 'super_admin':
        messages.error(request, 'Access denied.')
        return redirect('homepage')
    
    # Get analytics data
    total_schools = School.objects.count()
    total_teachers = Teacher.objects.count()
    total_students = Student.objects.count()
    
    # School type distribution - use Count import
    school_types = School.objects.values('school_type').annotate(count=Count('id'))
    
    # Subscription distribution
    subscription_types = School.objects.values('subscription_type').annotate(count=Count('id'))
    
    # Recent schools
    recent_schools = School.objects.order_by('-created_at')[:5]
    
    context = {
        'total_schools': total_schools,
        'total_teachers': total_teachers,
        'total_students': total_students,
        'school_types': school_types,
        'subscription_types': subscription_types,
        'recent_schools': recent_schools,
    }
    return render(request, 'schools/admin_analytics.html', context)

@login_required
def school_analytics(request):
    """School-specific analytics for school admins"""
    school_admin = get_object_or_404(SchoolAdmin, user=request.user)
    school = school_admin.school
    
    # Basic counts
    teachers_count = Teacher.objects.filter(school=school).count()
    students_count = Student.objects.filter(school=school).count()
    
    # Class level distribution - use Count import
    class_distribution = Student.objects.filter(school=school).values(
        'class_level__name'
    ).annotate(
        count=Count('id')
    ).order_by('class_level__level')
    
    # Recent activity
    recent_assignments = Assignment.objects.filter(
        teacher__school=school
    ).order_by('-created_at')[:5]
    
    context = {
        'school': school,
        'teachers_count': teachers_count,
        'students_count': students_count,
        'class_distribution': class_distribution,
        'recent_assignments': recent_assignments,
        'is_senior_admin': school_admin.is_senior,
    }
    return render(request, 'schools/school_analytics.html', context)

@login_required
def payment_history(request):
    school_admin = get_object_or_404(SchoolAdmin, user=request.user)
    school = school_admin.school
    
    payments = Payment.objects.filter(school=school).order_by('-payment_date')
    
    # Handle case where subscription doesn't exist yet
    try:
        subscription = Subscription.objects.get(school=school)
    except Subscription.DoesNotExist:
        # Create a default subscription if none exists
        subscription = Subscription.objects.create(
            school=school,
            start_date=timezone.now().date(),
            end_date=timezone.now().date() + timezone.timedelta(days=365),  # 1 year default
            is_active=True
        )
    
    context = {
        'school': school,
        'payments': payments,
        'subscription': subscription,
        'is_senior_admin': school_admin.is_senior,
    }
    return render(request, 'schools/payment_history.html', context)


@login_required
def upgrade_subscription(request):
    school_admin = get_object_or_404(SchoolAdmin, user=request.user)
    
    if not school_admin.is_senior:
        messages.error(request, 'Only senior admins can upgrade subscriptions.')
        return redirect('schools:dashboard')
    
    school = school_admin.school
    
    if request.method == 'POST':
        new_subscription_type = request.POST.get('subscription_type')
        school.subscription_type = new_subscription_type
        school.save()
        
        messages.success(request, f'Subscription upgraded to {school.get_subscription_type_display()}!')
        return redirect('schools:payment_history')
    
    return render(request, 'schools/upgrade_subscription.html', {
        'school': school,
    })


@login_required
def assign_subjects_to_teacher(request, teacher_id):
    school_admin = get_object_or_404(SchoolAdmin, user=request.user)
    
    if not school_admin.is_senior:
        messages.error(request, "Only senior admins can assign subjects.")
        return redirect('schools:manage_users')
    
    teacher = get_object_or_404(Teacher, id=teacher_id, school=school_admin.school)
    
    # Get all subjects and group by category
    subjects = Subject.objects.all().order_by('category', 'name')
    subject_categories = {}
    
    for subject in subjects:
        if subject.category not in subject_categories:
            subject_categories[subject.category] = []
        subject_categories[subject.category].append(subject)
    
    if request.method == 'POST':
        selected_subjects = request.POST.getlist('subjects')
        teacher.subjects.set(selected_subjects)
        messages.success(request, f'Subjects assigned to {teacher.user.get_full_name()} successfully!')
        return redirect('schools:manage_users')
    
    return render(request, 'schools/assign_subjects.html', {
        'teacher': teacher.user,
        'subject_categories': subject_categories,
        'school': school_admin.school
    })

@login_required
def fee_management(request):
    school_admin = get_object_or_404(SchoolAdmin, user=request.user)
    school = school_admin.school
    
    students = Student.objects.filter(school=school)
    fee_structures = FeeStructure.objects.filter(school=school, is_active=True)
    
    # Get fee summary
    fee_summary = []
    for student in students:
        total_fees = StudentFee.objects.filter(student=student).aggregate(
            total_due=models.Sum('amount_due'),
            total_paid=models.Sum('amount_paid')
        )
        fee_summary.append({
            'student': student,
            'total_due': total_fees['total_due'] or 0,
            'total_paid': total_fees['total_paid'] or 0,
            'balance': (total_fees['total_due'] or 0) - (total_fees['total_paid'] or 0)
        })
    
    context = {
        'school': school,
        'fee_summary': fee_summary,
        'fee_structures': fee_structures,
        'is_senior_admin': school_admin.is_senior,
    }
    return render(request, 'schools/fee_management.html', context)
@login_required
def assign_subjects_to_teacher(request, teacher_id):
    school_admin = get_object_or_404(SchoolAdmin, user=request.user)
    
    if not school_admin.is_senior:
        messages.error(request, "Only senior admins can assign subjects.")
        return redirect('schools:manage_users')
    
    teacher = get_object_or_404(Teacher, id=teacher_id, school=school_admin.school)
    subjects = Subject.objects.all()
    
    if request.method == 'POST':
        selected_subjects = request.POST.getlist('subjects')
        teacher.subjects.set(selected_subjects)
        messages.success(request, f'Subjects assigned to {teacher.user.get_full_name()} successfully!')
        return redirect('schools:manage_users')
    
    return render(request, 'schools/assign_subjects.html', {
        'teacher': teacher,
        'subjects': subjects,
        'school': school_admin.school
    })