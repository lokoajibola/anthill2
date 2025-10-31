from django.shortcuts import render, get_object_or_404
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .models import School, SchoolAdmin, Payment, Subscription, StudentFee, GalleryImage, Article, AdmissionInfo
from django.contrib import messages
from django.db.models import Q, Count
from users.models import User, Teacher, Student
from users.forms import CreateUserForm
from django.utils import timezone  # Add timezone import
from academic.models import ClassLevel, Assignment, FeeStructure, Subject, ClassSubject
# from .schools.model import StudentFee
from django.contrib.auth import logout
from users.forms import SubjectForm
from users.forms import UserProfileForm
from datetime import timedelta
from decimal import Decimal
from django.http import JsonResponse

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
        
        # Add about_text if the field exists
        if hasattr(school, 'about_text'):
            school.about_text = request.POST.get('about_text', school.about_text)
        
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
    
    # Get all the data for homepage
    gallery_images = GalleryImage.objects.filter(school=school)
    articles = Article.objects.filter(school=school).order_by('-created_at')
    admission_info = AdmissionInfo.objects.filter(school=school).first()
    
    return render(request, 'schools/school_homepage.html', {
        'school': school,
        'gallery_images': gallery_images,
        'articles': articles,
        'admission_info': admission_info
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
    
    print(f"=== MANAGE CLASSES DEBUG ===")
    print(f"User: {request.user.username}")
    print(f"User type: {request.user.user_type}")
    print(f"School Admin: {school_admin}")
    print(f"Is Senior Admin: {school_admin.is_senior}")
    
    classes = ClassLevel.objects.filter(school=school)
    print(f"Classes found: {classes.count()}")
    
    context = {
        'school': school,
        'classes': classes,
        'is_senior_admin': school_admin.is_senior,  # Make sure this is passed
    }
    
    print(f"Context is_senior_admin: {school_admin.is_senior}")
    return render(request, 'schools/manage_classes.html', context)


@login_required
def create_class(request):
    school_admin = get_object_or_404(SchoolAdmin, user=request.user)
    school = school_admin.school
    
    if not school_admin.is_senior:
        messages.error(request, "Only senior admins can create classes.")
        return redirect('schools:manage_classes')
    
    if request.method == 'POST':
        name = request.POST.get('name')
        level = request.POST.get('level')
        # Remove description since model doesn't have it
        # description = request.POST.get('description', '')
        
        # Check if class with same name already exists in this school
        if ClassLevel.objects.filter(name=name, school=school).exists():
            messages.error(request, f'A class with name "{name}" already exists in this school.')
            return render(request, 'schools/create_class.html', {'school': school})
        
        # Create the class without description
        ClassLevel.objects.create(
            name=name,
            level=level,
            # description=description,  # Remove this
            school=school
        )
        messages.success(request, f'Class "{name}" created successfully!')
        return redirect('schools:manage_classes')
    
    return render(request, 'schools/create_class.html', {
        'school': school
    })

@login_required
def manage_fees(request):
    school_admin = get_object_or_404(SchoolAdmin, user=request.user)
    school = school_admin.school
    
    # Remove is_active filter - FeeStructure doesn't have this field
    fee_structures = FeeStructure.objects.filter(school=school)
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
    
    # Add payment history query if you have a FeePayment model
    # payment_history = FeePayment.objects.filter(student_fee__student=student).order_by('-payment_date')
    
    if request.method == 'POST':
        if 'mark_paid' in request.POST:
            student_fee_id = request.POST.get('student_fee_id')
            student_fee = get_object_or_404(StudentFee, id=student_fee_id, student=student)
            
            # Create payment record
            receipt_number = f"RCP{student_fee.id}{timezone.now().strftime('%Y%m%d%H%M%S')}"
            # FeePayment.objects.create(...) - Uncomment if you have FeePayment model
            
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
            # FeePayment.objects.create(...) - Uncomment if you have FeePayment model
            
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
        'total_balance': total_balance,
        'is_senior_admin': school_admin.is_senior,
        # 'payment_history': payment_history,  # Uncomment if you have FeePayment model
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
        
        # Update subject type (compulsory/elective)
        if 'subject_id' in request.POST and 'is_compulsory' in request.POST:
            subject_id = request.POST.get('subject_id')
            is_compulsory = request.POST.get('is_compulsory') == 'on'
            
            class_subject = get_object_or_404(ClassSubject, id=subject_id, class_level=class_level)
            class_subject.is_compulsory = is_compulsory
            class_subject.save()
            messages.success(request, f'{class_subject.subject.name} updated to {"Compulsory" if is_compulsory else "Elective"}!')
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
def manage_class_teachers(request, class_id):
    school_admin = get_object_or_404(SchoolAdmin, user=request.user)
    class_level = get_object_or_404(ClassLevel, id=class_id, school=school_admin.school)
    
    # Get all teachers in the school
    all_teachers = Teacher.objects.filter(school=school_admin.school).select_related('user')
    
    # Get currently assigned teachers for this class
    assigned_teachers = Teacher.objects.filter(
        classsubject__class_level=class_level
    ).distinct().select_related('user')
    
    # Get assigned subjects for each teacher in this class
    teacher_subjects = {}
    for teacher in assigned_teachers:
        subjects = Subject.objects.filter(
            classsubject__class_level=class_level,
            classsubject__teacher=teacher
        )
        teacher_subjects[teacher.id] = subjects
    
    if request.method == 'POST':
        if 'assign_teacher' in request.POST:
            teacher_id = request.POST.get('teacher')
            subject_ids = request.POST.getlist('subjects')
            
            if teacher_id and subject_ids:
                teacher = get_object_or_404(Teacher, id=teacher_id, school=school_admin.school)
                
                # Assign subjects to teacher for this class
                for subject_id in subject_ids:
                    subject = get_object_or_404(Subject, id=subject_id)
                    
                    # Create or update ClassSubject
                    ClassSubject.objects.update_or_create(
                        class_level=class_level,
                        subject=subject,
                        defaults={'teacher': teacher}
                    )
                    
                    # Also add to teacher's direct subjects
                    teacher.subjects.add(subject)
                
                messages.success(request, f'Teacher {teacher.user.get_full_name()} assigned to class!')
                return redirect('schools:manage_class_teachers', class_id=class_id)
                
        elif 'remove_teacher' in request.POST:
            teacher_id = request.POST.get('teacher_id')
            teacher = get_object_or_404(Teacher, id=teacher_id, school=school_admin.school)
            
            # Remove teacher from all subjects in this class
            ClassSubject.objects.filter(
                class_level=class_level,
                teacher=teacher
            ).update(teacher=None)
            
            messages.success(request, f'Teacher {teacher.user.get_full_name()} removed from class!')
            return redirect('schools:manage_class_teachers', class_id=class_id)
        
        elif 'remove_subject' in request.POST:
            teacher_id = request.POST.get('teacher_id')
            subject_id = request.POST.get('subject_id')
            
            teacher = get_object_or_404(Teacher, id=teacher_id, school=school_admin.school)
            subject = get_object_or_404(Subject, id=subject_id)
            
            # Remove teacher from specific subject in this class
            ClassSubject.objects.filter(
                class_level=class_level,
                subject=subject,
                teacher=teacher
            ).update(teacher=None)
            
            messages.success(request, f'Teacher removed from {subject.name}!')
            return redirect('schools:manage_class_teachers', class_id=class_id)
    
    # Get available subjects for this class (not yet assigned to any teacher)
    assigned_subject_ids = ClassSubject.objects.filter(
        class_level=class_level,
        teacher__isnull=False
    ).values_list('subject_id', flat=True)
    
    available_subjects = Subject.objects.exclude(id__in=assigned_subject_ids)
    
    context = {
        'school': school_admin.school,
        'class_level': class_level,
        'all_teachers': all_teachers,
        'assigned_teachers': assigned_teachers,
        'teacher_subjects': teacher_subjects,
        'available_subjects': available_subjects,
        'is_senior_admin': school_admin.is_senior,
    }
    return render(request, 'schools/manage_class_teachers.html', context)

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
    search_query = request.GET.get('q', '')
    
    if not school_admin.is_senior:
        return redirect('schools:dashboard')
    
    school = school_admin.school
    teachers = User.objects.filter(teacher__school=school) if hasattr(User, 'teacher') else []
    students = User.objects.filter(student__school=school) if hasattr(User, 'student') else []
    junior_admins = SchoolAdmin.objects.filter(school=school, is_senior=False)
    
    # Apply search filter
    if search_query:
        teachers = teachers.filter(
            Q(first_name__icontains=search_query) | 
            Q(last_name__icontains=search_query) |
            Q(email__icontains=search_query)
        )
        students = students.filter(
            Q(first_name__icontains=search_query) | 
            Q(last_name__icontains=search_query) |
            Q(email__icontains=search_query)
        )

    context = {
        'school': school,
        'teachers': teachers,
        'students': students,
        'junior_admins': junior_admins,
    }
    return render(request, 'schools/manage_users.html', context)

@login_required
def verify_payment(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        reference = data.get('reference')
        amount = data.get('amount')
        description = data.get('description')
        
        # Verify with Paystack
        headers = {'Authorization': f'Bearer {settings.PAYSTACK_SECRET_KEY}'}
        response = requests.get(f'https://api.paystack.co/transaction/verify/{reference}', headers=headers)
        
        if response.status_code == 200:
            result = response.json()
            if result['data']['status'] == 'success':
                school = request.user.schooladmin.school
                subscription = Subscription.objects.get(school=school)
                
                # Calculate days based on amount
                if amount == 18000:
                    days = 730  # 2 years
                else:
                    days = 365  # 1 year
                
                # Extend subscription
                subscription.end_date = subscription.end_date + timezone.timedelta(days=days)
                subscription.save()
                
                # Record payment
                Payment.objects.create(
                    school=school,
                    amount=amount,
                    status='completed',
                    payment_date=timezone.now(),
                    description=description,
                    reference=reference
                )
                
                return JsonResponse({'success': True})
        
        return JsonResponse({'success': False, 'error': 'Payment verification failed'})

@login_required
def user_profile(request, user_type, user_id):
    # Initialize variables
    school = None
    can_edit = False
    
    # Check if user is a school admin, otherwise get their school from their profile
    try:
        school_admin_obj = SchoolAdmin.objects.get(user=request.user)
        school = school_admin_obj.school
        can_edit = school_admin_obj.is_senior
    except SchoolAdmin.DoesNotExist:
        # If user is not an admin, get school from their profile
        if request.user.user_type == 'teacher':
            profile_obj = get_object_or_404(Teacher, user=request.user)
            school = profile_obj.school
        elif request.user.user_type == 'student':
            profile_obj = get_object_or_404(Student, user=request.user)
            school = profile_obj.school
        else:
            messages.error(request, "Access denied.")
            return redirect('core:homepage')
    
    # Ensure school is set
    if not school:
        messages.error(request, "Unable to determine school.")
        return redirect('core:homepage')
    
    if user_type == 'teacher':
        user = get_object_or_404(User, id=user_id, user_type='teacher', school=school)
        profile = get_object_or_404(Teacher, user=user)
    elif user_type == 'student':
        user = get_object_or_404(User, id=user_id, user_type='student', school=school)
        profile = get_object_or_404(Student, user=user)
    else:
        user = get_object_or_404(User, id=user_id, school=school)
        profile = get_object_or_404(SchoolAdmin, user=user)
    
    if request.method == 'POST':
        # Handle profile picture upload
        if 'profile_picture' in request.FILES:
            user.profile_picture = request.FILES['profile_picture']
            user.save()
            messages.success(request, 'Profile picture updated successfully!')
            return redirect('schools:user_profile', user_type=user_type, user_id=user_id)
        
        # Handle form data - use can_edit variable instead of school_admin
        if can_edit:
            form = UserProfileForm(request.POST, instance=profile, user_type=user_type)
            if form.is_valid():
                form.save()
                messages.success(request, 'Profile updated successfully!')
                return redirect('schools:user_profile', user_type=user_type, user_id=user_id)
    else:
        form = UserProfileForm(instance=profile, user_type=user_type)
    
    context = {
        'user': user,
        'profile': profile,
        'form': form,
        'user_type': user_type,
        'school': school,
        'can_edit': can_edit,
    }
    return render(request, 'schools/user_profile.html', context)

@login_required
def fee_management(request):
    school_admin = get_object_or_404(SchoolAdmin, user=request.user)
    students = Student.objects.filter(school=school_admin.school).select_related('user', 'class_level')
    
    # Calculate fee totals for each student
    student_fees = []
    for student in students:
        total_due = 0
        total_paid = 0
        
        if student.class_level:
            # Remove is_active filter since FeeStructure doesn't have this field
            fee_structures = FeeStructure.objects.filter(class_level=student.class_level)
            
            for fee_structure in fee_structures:
                total_due += fee_structure.total_fee
                # Get or create student fee record
                student_fee, created = StudentFee.objects.get_or_create(
                    student=student,
                    fee_structure=fee_structure,
                    defaults={
                        'amount_due': fee_structure.total_fee,
                        'amount_paid': 0,
                        'payment_status': 'pending',
                        'due_date': timezone.now().date() + timedelta(days=30)
                    }
                )
                total_paid += student_fee.amount_paid
        
        student_fees.append({
            'student': student,
            'total_due': total_due,
            'total_paid': total_paid,
            'balance': total_due - total_paid,
            'status': 'Paid' if total_paid >= total_due else 'Unpaid'
        })
    
    context = {
        'school': school_admin.school,
        'student_fees': student_fees,
        'is_senior_admin': school_admin.is_senior,
    }
    return render(request, 'schools/fee_management.html', context)


@login_required
def create_fees(request):
    school_admin = get_object_or_404(SchoolAdmin, user=request.user)
    
    if not school_admin.is_senior:
        messages.error(request, "Only senior admins can create fees.")
        return redirect('schools:fee_management')
    
    class_levels = ClassLevel.objects.filter(school=school_admin.school)
    
    if request.method == 'POST':
        class_level_id = request.POST.get('class_level')
        fee_items = request.POST.getlist('fee_items[]')
        amounts = request.POST.getlist('amounts[]')
        
        if class_level_id and fee_items:
            class_level = get_object_or_404(ClassLevel, id=class_level_id, school=school_admin.school)
            total_amount = sum(float(amount) for amount in amounts if amount)
            
            # Check if fee structure already exists for this class and academic year
            academic_year = "2024-2025"  # Make this dynamic if needed
            fee_structure, created = FeeStructure.objects.get_or_create(
                class_level=class_level,
                academic_year=academic_year,
                defaults={
                    'tuition_fee': total_amount,
                    'total_fee': total_amount
                }
            )
            
            if not created:
                # Update existing fee structure
                fee_structure.tuition_fee = total_amount
                fee_structure.total_fee = total_amount
                fee_structure.save()
                messages.info(request, f'Fees updated for {class_level.name}!')
            else:
                messages.success(request, f'Fees created for {class_level.name} successfully!')
            
            # Assign fees to all students in that class
            students = Student.objects.filter(class_level=class_level, school=school_admin.school)
            for student in students:
                student_fee, fee_created = StudentFee.objects.get_or_create(
                    student=student,
                    fee_structure=fee_structure,
                    defaults={
                        'amount_due': total_amount,
                        'amount_paid': 0,
                        'payment_status': 'pending',
                        'due_date': timezone.now().date() + timedelta(days=30)
                    }
                )
                
                if not fee_created:
                    # Update existing student fee
                    student_fee.amount_due = total_amount
                    student_fee.save()
            
            return redirect('schools:fee_management')
    
    context = {
        'school': school_admin.school,
        'class_levels': class_levels,
    }
    return render(request, 'schools/create_fees.html', context)

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
def add_article(request):
    if request.method == 'POST':
        school_admin = get_object_or_404(SchoolAdmin, user=request.user)
        title = request.POST.get('title')
        content = request.POST.get('content')
        
        Article.objects.create(
            school=school_admin.school,
            title=title,
            content=content,
            author=request.user
        )
        messages.success(request, 'Article published!')
    return redirect('schools:edit_homepage')

@login_required
def manage_about(request):
    school_admin = get_object_or_404(SchoolAdmin, user=request.user)
    school = school_admin.school
    
    if request.method == 'POST':
        school.about_text = request.POST.get('about_text')
        school.vision = request.POST.get('vision')
        school.mission = request.POST.get('mission')
        school.motto = request.POST.get('motto')
        school.save()
        messages.success(request, 'About us information updated successfully!')
        return redirect('schools:manage_about')
    
    return render(request, 'schools/manage_about_us.html', {
        'school': school,
        'is_senior_admin': school_admin.is_senior
    })

@login_required
def manage_news(request):
    school_admin = get_object_or_404(SchoolAdmin, user=request.user)
    school = school_admin.school
    articles = Article.objects.filter(school=school).order_by('-created_at')
    
    return render(request, 'schools/manage_news.html', {
        'school': school,
        'articles': articles,
        'is_senior_admin': school_admin.is_senior
    })

@login_required
def edit_article(request, article_id):
    article = get_object_or_404(Article, id=article_id, school=request.user.schooladmin.school)
    
    if request.method == 'POST':
        article.title = request.POST.get('title')
        article.content = request.POST.get('content')
        article.save()
        messages.success(request, 'Article updated successfully!')
    
    return redirect('schools:manage_news')

@login_required
def delete_article(request, article_id):
    article = get_object_or_404(Article, id=article_id, school=request.user.schooladmin.school)
    article.delete()
    messages.success(request, 'Article deleted successfully!')
    return redirect('schools:manage_news')

# @login_required
# def update_about(request):
#     if request.method == 'POST':
#         school_admin = get_object_or_404(SchoolAdmin, user=request.user)
#         school = school_admin.school
#         school.about_text = request.POST.get('about_text')
#         school.save()
#         messages.success(request, 'About us updated!')
#     return redirect('schools:edit_homepage')


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
def make_payment(request):
    school_admin = get_object_or_404(SchoolAdmin, user=request.user)
    school = school_admin.school
    
    try:
        subscription = Subscription.objects.get(school=school)
    except Subscription.DoesNotExist:
        subscription = Subscription.objects.create(
            school=school,
            start_date=timezone.now().date(),
            end_date=timezone.now().date() + timezone.timedelta(days=365),
            is_active=True
        )
    
    context = {
        'school': school,
        'subscription': subscription,
        'is_senior_admin': school_admin.is_senior,
    }
    return render(request, 'schools/make_payment.html', context)

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


# @login_required
# def assign_subjects_to_teacher(request, teacher_id):
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
def delete_user(request, user_type, user_id):
    if request.method == 'POST':
        try:
            school_admin = request.user.schooladmin
            school = school_admin.school
            
            if user_type == 'teacher':
                user = get_object_or_404(Teacher, id=user_id, school=school)
            elif user_type == 'student':
                user = get_object_or_404(Student, id=user_id, school=school)
            elif user_type == 'admin':
                user = get_object_or_404(SchoolAdmin, id=user_id, school=school)
            else:
                return JsonResponse({'error': 'Invalid user type'}, status=400)
            
            # Delete the associated User object
            user_account = user.user
            user.delete()
            user_account.delete()
            
            return JsonResponse({'success': True})
            
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    
    return JsonResponse({'error': 'Method not allowed'}, status=405)

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


@login_required
def mark_fee_paid(request, student_id):
    if request.method == 'POST':
        try:
            student = get_object_or_404(Student, id=student_id, school=request.user.schooladmin.school)
            fee_record = StudentFee.objects.get(student=student)
            
            # Set balance to 0 and mark as paid
            fee_record.total_paid = fee_record.total_due
            fee_record.balance = 0
            fee_record.status = 'Paid'
            fee_record.save()
            
            return JsonResponse({'success': True})
            
        except StudentFee.DoesNotExist:
            return JsonResponse({'error': 'Fee record not found'}, status=404)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    
    return JsonResponse({'error': 'Method not allowed'}, status=405)