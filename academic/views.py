from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Subject, Assignment, StudentAssignment, Result, ClassLevel
from django.utils import timezone
from users.models import Teacher, Student
# from academic.models import ClassLevel

@login_required
def submit_assignment(request, assignment_id):
    student = get_object_or_404(Student, user=request.user)
    student_assignment = get_object_or_404(StudentAssignment, id=assignment_id, student=student)
    
    if request.method == 'POST':
        submitted_text = request.POST.get('submitted_text')
        submitted_file = request.FILES.get('submitted_file')
        
        student_assignment.submitted_text = submitted_text
        if submitted_file:
            student_assignment.submitted_file = submitted_file
        student_assignment.is_submitted = True
        student_assignment.submitted_at = timezone.now()
        student_assignment.save()
        
        messages.success(request, 'Assignment submitted successfully!')
        return redirect('academic:student_assignments')
    
    return render(request, 'academic/submit_assignment.html', {
        'student_assignment': student_assignment,
        'school': student.school
    })

@login_required
def teacher_subjects(request):
    teacher = get_object_or_404(Teacher, user=request.user)
    
    # Just use the direct subjects relationship
    subjects = teacher.subjects.all()
    
    print(f"DEBUG: Teacher {teacher.user.username} has {subjects.count()} subjects")
    for subject in subjects:
        print(f"DEBUG: - {subject.name}")
    
    return render(request, 'academic/teacher_subjects.html', {
        'teacher': teacher,
        'subjects': subjects,  # Simple direct relationship
        'school': teacher.school
    })

@login_required
def teacher_assignments(request):
    teacher = get_object_or_404(Teacher, user=request.user)
    assignments = Assignment.objects.filter(teacher=teacher).order_by('-created_at')
    
    return render(request, 'academic/teacher_assignments.html', {
        'teacher': teacher,
        'assignments': assignments,
        'school': teacher.school
    })

@login_required
def teacher_students(request):
    teacher = get_object_or_404(Teacher, user=request.user)
    
    # Get students from the teacher's school
    students = Student.objects.filter(school=teacher.school).select_related('user', 'class_level')
    
    # Filter by class level if provided
    class_level_filter = request.GET.get('class_level')
    if class_level_filter:
        students = students.filter(class_level_id=class_level_filter)
    
    class_levels = ClassLevel.objects.filter(school=teacher.school)
    
    return render(request, 'academic/teacher_students.html', {
        'teacher': teacher,
        'students': students,
        'class_levels': class_levels,
        'school': teacher.school,
        'selected_class_level': class_level_filter
    })

@login_required
def teacher_assignments(request):
    teacher = get_object_or_404(Teacher, user=request.user)
    assignments = Assignment.objects.filter(teacher=teacher).order_by('-created_at')
    
    return render(request, 'academic/teacher_assignments.html', {
        'teacher': teacher,
        'assignments': assignments,
        'school': teacher.school
    })

@login_required
def edit_assignment(request, assignment_id):
    teacher = get_object_or_404(Teacher, user=request.user)
    assignment = get_object_or_404(Assignment, id=assignment_id, teacher=teacher)
    
    if request.method == 'POST':
        assignment.title = request.POST.get('title')
        assignment.description = request.POST.get('description')
        assignment.due_date = request.POST.get('due_date')
        assignment.max_score = request.POST.get('max_score')
        assignment.save()
        
        messages.success(request, 'Assignment updated successfully!')
        return redirect('academic:teacher_assignments')
    
    return render(request, 'academic/edit_assignment.html', {
        'assignment': assignment,
        'school': teacher.school
    })

@login_required
def create_assignment(request):
    teacher = get_object_or_404(Teacher, user=request.user)
    
    if request.method == 'POST':
        title = request.POST.get('title')
        description = request.POST.get('description')
        subject_id = request.POST.get('subject')
        due_date = request.POST.get('due_date')
        max_score = request.POST.get('max_score', 100)
        
        subject = get_object_or_404(Subject, id=subject_id)
        
        assignment = Assignment.objects.create(
            title=title,
            description=description,
            subject=subject,
            teacher=teacher,
            due_date=due_date,
            max_score=max_score
        )
        
        messages.success(request, 'Assignment created successfully!')
        return redirect('academic:teacher_assignments')
    
    subjects = teacher.subjects.all()
    return render(request, 'academic/create_assignment.html', {
        'teacher': teacher,
        'subjects': subjects,
        'school': teacher.school
    })

@login_required
def create_assignment(request):
    teacher = get_object_or_404(Teacher, user=request.user)
    
    if request.method == 'POST':
        title = request.POST.get('title')
        description = request.POST.get('description')
        subject_id = request.POST.get('subject')
        due_date = request.POST.get('due_date')
        max_score = request.POST.get('max_score', 100)
        
        subject = get_object_or_404(Subject, id=subject_id)
        
        assignment = Assignment.objects.create(
            title=title,
            description=description,
            subject=subject,
            teacher=teacher,
            due_date=due_date,
            max_score=max_score
        )
        
        # Create StudentAssignment records for all students in the school
        students = Student.objects.filter(school=teacher.school)
        for student in students:
            StudentAssignment.objects.create(
                assignment=assignment,
                student=student
            )
        
        messages.success(request, 'Assignment created successfully!')
        return redirect('academic:teacher_assignments')
    
    subjects = teacher.subjects.all()
    return render(request, 'academic/create_assignment.html', {
        'teacher': teacher,
        'subjects': subjects,
        'school': teacher.school
    })

@login_required
def upload_scores(request):
    teacher = get_object_or_404(Teacher, user=request.user)
    
    if request.method == 'POST':
        student_id = request.POST.get('student')
        subject_id = request.POST.get('subject')
        exam_type = request.POST.get('exam_type')
        score = request.POST.get('score')
        max_score = request.POST.get('max_score', 100)
        date_taken = request.POST.get('date_taken')
        
        student = get_object_or_404(Student, id=student_id, school=teacher.school)
        subject = get_object_or_404(Subject, id=subject_id)
        
        # Create or update result
        result, created = Result.objects.update_or_create(
            student=student,
            subject=subject,
            exam_type=exam_type,
            date_taken=date_taken,
            defaults={
                'score': score,
                'max_score': max_score,
                'recorded_by': teacher
            }
        )
        
        messages.success(request, f'Score uploaded for {student.user.get_full_name()}!')
        return redirect('academic:upload_scores')
    
    subjects = teacher.subjects.all()
    students = Student.objects.filter(school=teacher.school)
    
    return render(request, 'academic/upload_scores.html', {
        'teacher': teacher,
        'subjects': subjects,
        'students': students,
        'school': teacher.school
    })

@login_required
def teacher_subjects(request):
    teacher = get_object_or_404(Teacher, user=request.user)
    subjects = teacher.subjects.all()
    
    return render(request, 'academic/teacher_subjects.html', {
        'teacher': teacher,
        'subjects': subjects
    })

@login_required
def upload_scores(request):
    teacher = get_object_or_404(Teacher, user=request.user)
    
    if request.method == 'POST':
        # Handle score upload logic
        student_id = request.POST.get('student')
        subject_id = request.POST.get('subject')
        exam_type = request.POST.get('exam_type')
        score = request.POST.get('score')
        
        # Add your score upload logic here
        messages.success(request, 'Scores uploaded successfully!')
        return redirect('academic:upload_scores')
    
    subjects = teacher.subjects.all()
    # You'll need to get students based on the teacher's classes
    return render(request, 'academic/upload_scores.html', {
        'teacher': teacher,
        'subjects': subjects
    })

@login_required
def create_assignment(request):
    teacher = get_object_or_404(Teacher, user=request.user)
    
    if request.method == 'POST':
        title = request.POST.get('title')
        description = request.POST.get('description')
        subject_id = request.POST.get('subject')
        due_date = request.POST.get('due_date')
        max_score = request.POST.get('max_score', 100)
        
        subject = get_object_or_404(Subject, id=subject_id)
        
        assignment = Assignment.objects.create(
            title=title,
            description=description,
            subject=subject,
            teacher=teacher,
            due_date=due_date,
            max_score=max_score
        )
        # Create StudentAssignment records for all students in the school
        students = Student.objects.filter(school=teacher.school)
        for student in students:
            StudentAssignment.objects.create(
                assignment=assignment,
                student=student
            )
        
        messages.success(request, 'Assignment created successfully!')
        return redirect('academic:teacher_assignments')
    
    subjects = teacher.subjects.all()
    return render(request, 'academic/create_assignment.html', {
        'teacher': teacher,
        'subjects': subjects,
        'school': teacher.school
    })
@login_required
def student_assignments(request):
    student = get_object_or_404(Student, user=request.user)
    assignments = StudentAssignment.objects.filter(student=student)
    
    return render(request, 'academic/student_assignments.html', {
        'student': student,
        'assignments': assignments
    })

@login_required
def submit_assignment(request, assignment_id):
    student = get_object_or_404(Student, user=request.user)
    student_assignment = get_object_or_404(StudentAssignment, id=assignment_id, student=student)
    
    if request.method == 'POST':
        submitted_text = request.POST.get('submitted_text')
        submitted_file = request.FILES.get('submitted_file')
        
        student_assignment.submitted_text = submitted_text
        if submitted_file:
            student_assignment.submitted_file = submitted_file
        student_assignment.is_submitted = True
        student_assignment.submitted_at = timezone.now()
        student_assignment.save()
        
        messages.success(request, 'Assignment submitted successfully!')
        return redirect('academic:student_assignments')
    
    return render(request, 'academic/submit_assignment.html', {
        'student_assignment': student_assignment
    })

@login_required
def student_results(request):
    student = get_object_or_404(Student, user=request.user)
    results = Result.objects.filter(student=student).order_by('-date_taken')
    
    if request.user.user_type == 'student' and request.user != student.user:
        messages.error(request, "You don't have permission to view these results.")
        return redirect('academic:student_dashboard')

    return render(request, 'academic/student_results.html', {
        'student': student,
        'results': results
    })


@login_required
def student_assignments(request):
    student = get_object_or_404(Student, user=request.user)
    assignments = StudentAssignment.objects.filter(student=student).select_related('assignment')
    
    return render(request, 'academic/student_assignments.html', {
        'student': student,
        'assignments': assignments,
        'school': student.school
    })

@login_required
def submit_assignment(request, assignment_id):
    student = get_object_or_404(Student, user=request.user)
    student_assignment = get_object_or_404(StudentAssignment, id=assignment_id, student=student)
    
    if request.method == 'POST':
        submitted_text = request.POST.get('submitted_text')
        submitted_file = request.FILES.get('submitted_file')
        
        student_assignment.submitted_text = submitted_text
        if submitted_file:
            student_assignment.submitted_file = submitted_file
        student_assignment.is_submitted = True
        student_assignment.submitted_at = timezone.now()
        student_assignment.save()
        
        messages.success(request, 'Assignment submitted successfully!')
        return redirect('academic:student_assignments')
    
    return render(request, 'academic/submit_assignment.html', {
        'student_assignment': student_assignment,
        'school': student.school
    })

@login_required
def student_results(request):
    student = get_object_or_404(Student, user=request.user)
    results = Result.objects.filter(student=student).select_related('subject').order_by('-date_taken')
    
    # Calculate averages
    if results:
        total_score = sum(result.score for result in results)
        total_max_score = sum(result.max_score for result in results)
        average_percentage = (total_score / total_max_score) * 100 if total_max_score > 0 else 0
    else:
        average_percentage = 0
    
    return render(request, 'academic/student_results.html', {
        'student': student,
        'results': results,
        'average_percentage': average_percentage,
        'school': student.school
    })

@login_required
def student_fees(request):
    student = get_object_or_404(Student, user=request.user)
    
    student_fees = StudentFee.objects.filter(student=student).select_related('fee_structure')
    
    # Calculate totals
    total_due = sum(fee.amount_due for fee in student_fees)
    total_paid = sum(fee.amount_paid for fee in student_fees)
    total_balance = total_due - total_paid
    
    # Payment history
    payment_history = FeePayment.objects.filter(
        student_fee__student=student
    ).select_related('student_fee__fee_structure').order_by('-payment_date')
    
    return render(request, 'academic/student_fees.html', {
        'student': student,
        'student_fees': student_fees,
        'payment_history': payment_history,
        'total_due': total_due,
        'total_paid': total_paid,
        'total_balance': total_balance,
        'school': student.school
    })