from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Subject, Assignment, StudentAssignment, Result, ClassLevel, Result, ClassSubject  
from django.utils import timezone
from users.models import Teacher, Student
from schools.models import StudentFee, FeePayment
from django.views.decorators.http import require_http_methods
from django.http import JsonResponse
import json
from django.core.files.storage import FileSystemStorage
from django.conf import settings
import os

# from academic.models import ClassLevel

@login_required
def submit_assignment(request, student_assignment_id):
    student_assignment = get_object_or_404(StudentAssignment, id=student_assignment_id, student__user=request.user)
    
    if request.method == 'POST':
        # Check if assignment is already submitted
        if student_assignment.is_submitted:
            messages.error(request, 'Assignment has already been submitted.')
            return redirect('academic:student_assignments')
        
        # Check if due date has passed
        if timezone.now() > student_assignment.assignment.due_date:
            messages.error(request, 'Cannot submit assignment after due date.')
            return redirect('academic:student_assignments')
        
        # Handle file upload
        if 'submitted_file' in request.FILES:
            submitted_file = request.FILES['submitted_file']
            # Check file size (2MB limit)
            if submitted_file.size > 2 * 1024 * 1024:
                messages.error(request, 'File size must be less than 2MB.')
                return render(request, 'academic/submit_assignment.html', {
                    'student_assignment': student_assignment
                })
            
            student_assignment.submitted_file = submitted_file
            student_assignment.is_submitted = True
            student_assignment.submission_date = timezone.now()
            student_assignment.save()
            
            messages.success(request, 'Assignment submitted successfully!')
            return redirect('academic:student_assignments')
        else:
            messages.error(request, 'Please select a file to upload.')
    
    return render(request, 'academic/submit_assignment.html', {
        'student_assignment': student_assignment
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
        class_ids = request.POST.getlist('classes')
        
        subject = get_object_or_404(Subject, id=subject_id)
        
        assignment = Assignment(
            title=title,
            description=description,
            subject=subject,
            teacher=teacher,
            due_date=due_date,
            max_score=max_score
        )
        
        # Handle file upload
        if 'assignment_file' in request.FILES:
            assignment_file = request.FILES['assignment_file']
            # Check file size (2MB limit)
            if assignment_file.size > 2 * 1024 * 1024:
                messages.error(request, 'File size must be less than 2MB.')
                subjects = teacher.subjects.all()
                return render(request, 'academic/create_assignment.html', {
                    'teacher': teacher,
                    'subjects': subjects,
                    'school': teacher.school
                })
            assignment.assignment_file = assignment_file
        
        assignment.save()
        
        # Create StudentAssignment records for all students in the school
        students = Student.objects.filter(school=teacher.school, class_level_id__in=class_ids)
        for student in students:
            StudentAssignment.objects.create(
                assignment=assignment,
                student=student
            )
        
        messages.success(request, 'Assignment created successfully!')
        return redirect('academic:teacher_assignments')
    
    subjects = teacher.subjects.all()
    teacher = request.user.teacher
    school = teacher.school
        
    # classes = ClassLevel.objects.filter(school=teacher.school)
    classes = ClassLevel.objects.filter(
            classsubject__teacher=teacher,
            school=school
        ).distinct()
    return render(request, 'academic/create_assignment.html', {
        'teacher': teacher,
        'subjects': subjects,
        'classes': classes,
        'school': teacher.school
    })

@login_required
def assignment_submissions(request, assignment_id):
    assignment = get_object_or_404(Assignment, id=assignment_id, teacher=request.user.teacher)
    submissions = StudentAssignment.objects.filter(assignment=assignment)
    return render(request, 'academic/assignment_submissions.html', {
        'assignment': assignment,
        'submissions': submissions
    })

@login_required
def edit_assignment(request, assignment_id):
    assignment = get_object_or_404(Assignment, id=assignment_id, teacher=request.user.teacher)
    # Add edit logic here
    return redirect('academic:teacher_assignments')

@login_required
def delete_result(request, result_id):
    if request.method == 'DELETE':
        try:
            result = get_object_or_404(Result, id=result_id, recorded_by=request.user.teacher)
            result.delete()
            return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    return JsonResponse({'error': 'Method not allowed'}, status=405)

@login_required
def delete_assignment(request, assignment_id):
    assignment = get_object_or_404(Assignment, id=assignment_id, teacher=request.user.teacher)
    assignment.delete()
    messages.success(request, "Assignment deleted successfully")
    return redirect('academic:teacher_assignments')

@login_required
def students_by_class_subject(request):
    class_id = request.GET.get('class_id')
    subject_id = request.GET.get('subject_id')
    
    students = Student.objects.filter(
        class_level_id=class_id,
        elective_subjects_id=subject_id
    ).select_related('user')
    
    student_data = []
    for student in students:
        student_data.append({
            'id': student.id,
            'full_name': student.user.get_full_name(),
            'admission_number': student.admission_number,
        })
    
    return JsonResponse({'students': student_data})


def upload_scores_test(request):
    """Simple test view to check if data is being passed correctly"""
    teacher = request.user.teacher
    school = teacher.school
    
    # Get classes and subjects
    classes = ClassLevel.objects.filter(classsubject__teacher=teacher, school=school).distinct()
    teacher_subjects = Subject.objects.filter(classsubject__teacher=teacher).distinct()
    
    context = {
        'school': school,
        'classes': classes,
        'teacher_subjects': teacher_subjects,
    }
    
    return render(request, 'academic/upload_scores_simple.html', context)

@login_required
def upload_scores(request):
    try:
        teacher = request.user.teacher
        school = teacher.school
        
        # Get classes and subjects for the teacher
        classes = ClassLevel.objects.filter(classsubject__teacher=teacher, school=school).distinct()
        teacher_subjects = Subject.objects.filter(classsubject__teacher=teacher).distinct()
        
        students = []
        selected_class_id = request.GET.get('class_id')
        selected_subject_id = request.GET.get('subject_id')
        
        if request.method == 'POST':
            if 'upload_scores' in request.POST:
                class_id = request.POST.get('class_level')
                subject_id = request.POST.get('subject')
                exam_type = request.POST.get('exam_type')
                max_score = request.POST.get('max_score', 100)
                date_taken = request.POST.get('date_taken')
                
                success_count = 0
                for key, value in request.POST.items():
                    if key.startswith('score_') and value:
                        try:
                            student_id = key.replace('score_', '')
                            student = Student.objects.get(id=student_id, school=school)
                            subject = Subject.objects.get(id=subject_id)
                            
                            # Create or update result - using Result model
                            Result.objects.update_or_create(
                                student=student,
                                subject=subject,
                                exam_type=exam_type,
                                date_taken=date_taken,
                                recorded_by=teacher,  # Use recorded_by instead of teacher
                                defaults={
                                    'score': value,
                                    'max_score': max_score
                                }
                            )
                            success_count += 1
                        except Exception as e:
                            messages.error(request, f'Error saving score: {str(e)}')
                
                messages.success(request, f'Successfully uploaded {success_count} scores!')
                return redirect('academic:upload_scores')

        # Load students if class and subject are selected
        if selected_class_id and selected_subject_id:
            selected_class = ClassLevel.objects.get(id=selected_class_id, school=school)
            students = Student.objects.filter(class_level=selected_class, school=school).select_related('user')
        
        context = {
            'school': school,
            'classes': classes,
            'teacher_subjects': teacher_subjects,
            'students': students,
        }
        
        return render(request, 'academic/upload_scores.html', context)
        
    except Exception as e:
        print(f"Error: {e}")
        return render(request, 'academic/upload_scores.html', {
            'school': None,
            'classes': [],
            'teacher_subjects': [],
            'students': [],
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
    try:
        print("=== UPLOAD SCORES - DETAILED DEBUG ===")
        
        # Check user and teacher
        print(f"User: {request.user.username}")
        print(f"User type: {request.user.user_type}")
        
        if not hasattr(request.user, 'teacher'):
            print("ERROR: User has no teacher attribute")
            return render(request, 'academic/upload_scores.html', {
                'school': None,
                'classes': [],
                'teacher_subjects': [],
            })
        
        teacher = request.user.teacher
        print(f"Teacher: {teacher.user.get_full_name()} (ID: {teacher.id})")
        
        school = teacher.school
        print(f"School: {school.name} (ID: {school.id})")
        
        # Get classes and subjects for the teacher
        classes = ClassLevel.objects.filter(
            classsubject__teacher=teacher,
            school=school
        ).distinct()
        
        teacher_subjects = Subject.objects.filter(
            classsubject__teacher=teacher
        ).distinct()
        
        # Handle AJAX JSON request (from the new form)
        if request.method == 'POST' and request.content_type == 'application/json':
            try:
                data = json.loads(request.body)
                print("=== PROCESSING AJAX REQUEST ===")
                print(f"Received data: {data}")
                
                class_level_id = data.get('class_level')
                subject_id = data.get('subject')
                exam_type = data.get('exam_type')
                max_score = data.get('max_score')
                date_taken = data.get('date_taken')
                results_data = data.get('results', [])
                
                print(f"Class Level ID: {class_level_id}")
                print(f"Subject ID: {subject_id}")
                print(f"Exam Type: {exam_type}")
                print(f"Max Score: {max_score}")
                print(f"Date Taken: {date_taken}")
                print(f"Number of results: {len(results_data)}")
                
                # Validate required fields
                if not all([class_level_id, subject_id, exam_type, max_score, date_taken]):
                    return JsonResponse({
                        'success': False,
                        'error': 'Missing required fields'
                    })
                
                # Get subject
                subject = get_object_or_404(Subject, id=subject_id)
                
                created_count = 0
                errors = []
                
                for result_item in results_data:
                    try:
                        student_id = result_item.get('student_id')
                        score_value = result_item.get('score')
                        
                        print(f"Processing student ID: {student_id}, score: {score_value}")
                        
                        if not student_id or score_value is None or score_value == '':
                            errors.append(f"Missing student ID or score for one entry")
                            continue
                        
                        # Get student object
                        student = Student.objects.get(id=student_id)
                        
                        # Check if student belongs to the selected class
                        if student.class_level.id != int(class_level_id):
                            errors.append(f"Student {student.user.get_full_name()} is not in the selected class")
                            continue
                        
                        # Check if result already exists (based on unique_together constraint)
                        existing_result = Result.objects.filter(
                            student=student,
                            subject=subject,
                            exam_type=exam_type,
                            date_taken=date_taken
                        ).first()
                        
                        if existing_result:
                            # Update existing result
                            existing_result.score = score_value
                            existing_result.max_score = max_score
                            existing_result.save()
                            print(f"UPDATED Existing Result: {existing_result}")
                        else:
                            # Create new Result object
                            result = Result.objects.create(
                                student=student,
                                subject=subject,
                                exam_type=exam_type,
                                score=score_value,
                                max_score=max_score,
                                date_taken=date_taken,
                                recorded_by=teacher
                            )
                            print(f"CREATED New Result: {result}")
                        
                        created_count += 1
                        
                    except Student.DoesNotExist:
                        error_msg = f"Student with ID {student_id} does not exist"
                        errors.append(error_msg)
                        print(f"ERROR: {error_msg}")
                    except Exception as e:
                        error_msg = f"Error creating result for student {student_id}: {str(e)}"
                        errors.append(error_msg)
                        print(f"ERROR: {error_msg}")
                
                print(f"Successfully processed {created_count} results")
                print(f"Errors: {errors}")
                
                if errors:
                    return JsonResponse({
                        'success': False,
                        'error': '; '.join(errors[:5]),  # Limit error message length
                        'created_count': created_count,
                        'total_attempted': len(results_data)
                    })
                else:
                    return JsonResponse({
                        'success': True,
                        'message': f'Successfully uploaded {created_count} results',
                        'created_count': created_count
                    })
                
            except json.JSONDecodeError:
                return JsonResponse({
                    'success': False,
                    'error': 'Invalid JSON data'
                })
            except Exception as e:
                print(f"Exception in AJAX processing: {str(e)}")
                import traceback
                print(traceback.format_exc())
                return JsonResponse({
                    'success': False,
                    'error': f'Server error: {str(e)}'
                })
        
        # Handle regular form submission (old method - fallback)
        elif request.method == 'POST':
            print("=== PROCESSING REGULAR FORM SUBMISSION ===")
            
            # This handles the old form format if you still want to support it
            student_id = request.POST.get('student')
            subject_id = request.POST.get('subject')
            exam_type = request.POST.get('exam_type')
            score_value = request.POST.get('score')
            max_score = request.POST.get('max_score')
            date_taken = request.POST.get('date_taken')
            
            print(f"Regular form data - Student: {student_id}, Subject: {subject_id}")
            
            try:
                student = Student.objects.get(id=student_id)
                subject = Subject.objects.get(id=subject_id)
                
                # Create Result object
                result = Result.objects.create(
                    student=student,
                    subject=subject,
                    exam_type=exam_type,
                    score=score_value,
                    max_score=max_score,
                    date_taken=date_taken,
                    recorded_by=teacher
                )
                
                print(f"SUCCESS: Created Result - {result}")
                messages.success(request, f"Score uploaded successfully for {student.user.get_full_name()}")
                
            except Student.DoesNotExist:
                error_msg = f"Student with ID {student_id} does not exist"
                print(f"ERROR: {error_msg}")
                messages.error(request, error_msg)
            except Subject.DoesNotExist:
                error_msg = f"Subject with ID {subject_id} does not exist"
                print(f"ERROR: {error_msg}")
                messages.error(request, error_msg)
            except Exception as e:
                error_msg = f"Error uploading score: {str(e)}"
                print(f"ERROR: {error_msg}")
                messages.error(request, error_msg)
        

        recent_results = Result.objects.filter(
            recorded_by=teacher
        ).select_related('student__user', 'subject', 'student__class_level').order_by('-date_taken')[:10]
        # Prepare context for GET requests
        context = {
            'school': school,
            'classes': classes,
            'teacher_subjects': teacher_subjects,
            'recent_results': recent_results,
        }
        
        print("=== RENDERING TEMPLATE ===")
        return render(request, 'academic/upload_scores.html', context)
        
    except Exception as e:
        print(f"=== EXCEPTION in upload_scores ===")
        print(f"Error: {str(e)}")
        import traceback
        print(traceback.format_exc())
        
        # Return JSON error for AJAX requests
        if request.method == 'POST' and request.content_type == 'application/json':
            return JsonResponse({
                'success': False,
                'error': str(e)
            })
        
        # Return regular error for normal requests
        return render(request, 'academic/upload_scores.html', {
            'school': None,
            'classes': [],
            'teacher_subjects': [],
        })


# API view for getting class students
@login_required
@require_http_methods(["GET"])
def api_class_students(request, class_id):
    """API endpoint to get students for a specific class"""
    try:
        print(f"=== API CLASS STUDENTS - Class ID: {class_id} ===")
        
        if not hasattr(request.user, 'teacher'):
            return JsonResponse({'error': 'Unauthorized'}, status=403)
        
        teacher = request.user.teacher
        class_level = get_object_or_404(ClassLevel, id=class_id, school=teacher.school)
        
        # Get students ONLY from the selected class
        students = Student.objects.filter(
            class_level=class_level,  # This ensures we only get students from the selected class
            school=teacher.school
        ).select_related('user', 'class_level')
        
        students_data = []
        for student in students:
            students_data.append({
                'id': student.id,
                'full_name': student.user.get_full_name(),
                'admission_number': getattr(student, 'admission_number', 'N/A'),
                'class_name': student.class_level.name,
            })
        
        print(f"Found {len(students_data)} students for class {class_level.name}")
        
        return JsonResponse({
            'students': students_data,
            'class_name': class_level.name,  # Return the actual class name
            'total_students': len(students_data)
        })
        
    except Exception as e:
        print(f"Error in api_class_students: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)

# API view for getting class subjects


@login_required
@require_http_methods(["GET"])
def api_class_subjects(request, class_id):
    """API endpoint to get subjects for a specific class taught by the teacher"""
    try:
        print(f"=== API CLASS SUBJECTS - Class ID: {class_id} ===")
        
        if not hasattr(request.user, 'teacher'):
            return JsonResponse({'error': 'Unauthorized'}, status=403)
        
        teacher = request.user.teacher
        class_level = get_object_or_404(ClassLevel, id=class_id, school=teacher.school)
        
        # Get subjects that this teacher teaches for this class
        subjects = Subject.objects.filter(
            classsubject__class_level=class_level,
            classsubject__teacher=teacher
        ).distinct()
        
        subjects_data = []
        for subject in subjects:
            subjects_data.append({
                'id': subject.id,
                'name': subject.name,
                'code': getattr(subject, 'code', ''),
            })
        
        print(f"Found {len(subjects_data)} subjects for class {class_level.name}")
        
        return JsonResponse({
            'subjects': subjects_data,
            'class_name': class_level.name,
            'total_subjects': len(subjects_data)
        })
        
    except Exception as e:
        print(f"Error in api_class_subjects: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)

@login_required
def view_results(request):
    teacher = get_object_or_404(Teacher, user=request.user)
    school = teacher.school
    
    results = Result.objects.filter(recorded_by=teacher).select_related(
        'student__user', 'subject', 'student__class_level'
    )
    
    # Filters
    class_id = request.GET.get('class_id')
    subject_id = request.GET.get('subject_id')
    exam_type = request.GET.get('exam_type')
    
    if class_id:
        results = results.filter(student__class_level_id=class_id)
    if subject_id:
        results = results.filter(subject_id=subject_id)
    if exam_type:
        results = results.filter(exam_type=exam_type)
    
    # Filter options
    classes = ClassLevel.objects.filter(school=school).distinct()
    subjects = Subject.objects.filter(classsubject__teacher=teacher).distinct()
    
    context = {
        'school': school,
        'results': results.order_by('-date_taken'),
        'classes': classes,
        'subjects': subjects,
        'selected_class': class_id,
        'selected_subject': subject_id,
        'selected_exam_type': exam_type,
    }
    return render(request, 'academic/view_results.html', context)

@login_required
def edit_result(request, result_id):
    result = get_object_or_404(Result, id=result_id, recorded_by=request.user.teacher)
    
    if request.method == 'POST':
        result.score = request.POST.get('score')
        result.max_score = request.POST.get('max_score')
        result.exam_type = request.POST.get('exam_type')
        result.date_taken = request.POST.get('date_taken')
        result.comment = request.POST.get('comment', '')
        result.save()
        messages.success(request, "Result updated successfully")
        return redirect('/academic/view-results/')
    
    return render(request, 'academic/edit_result.html', {'result': result})


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
def view_scores(request):
    teacher = get_object_or_404(Teacher, user=request.user)
    school = teacher.school
    
    # Get all results for subjects this teacher recorded
    results = Result.objects.filter(
        recorded_by=teacher
    ).select_related('student__user', 'subject', 'student__class_level').order_by('-date_taken')
    
    # Filter options
    class_id = request.GET.get('class_id')
    subject_id = request.GET.get('subject_id')
    exam_type = request.GET.get('exam_type')
    
    if class_id:
        results = results.filter(student__class_level_id=class_id)
    
    if subject_id:
        results = results.filter(subject_id=subject_id)
    
    if exam_type:
        results = results.filter(exam_type=exam_type)
    
    # Get filter options
    classes = ClassLevel.objects.filter(
        classsubject__teacher=teacher,
        school=school
    ).distinct()
    
    subjects = Subject.objects.filter(
        classsubject__teacher=teacher
    ).distinct()
    
    context = {
        'school': school,
        'scores': results,  # Now passing results instead of scores
        'classes': classes,
        'subjects': subjects,
        'selected_class_id': class_id,
        'selected_subject_id': subject_id,
        'selected_exam_type': exam_type,
    }
    return render(request, 'academic/view_scores.html', context)


@login_required
def student_dashboard(request):
    if not hasattr(request.user, 'student'):
        messages.error(request, "You must be a student to access this page.")
        return redirect('core:homepage')
    
    student = request.user.student
    school = student.school
    
    # Get recent results for the student - using Result model
    recent_scores = Result.objects.filter(student=student).select_related('subject').order_by('-date_taken')[:5]
    
    # Get subject count
    subject_count = Subject.objects.filter(result__student=student).distinct().count()
    
    # Calculate average score
    results = Result.objects.filter(student=student)
    if results.exists():
        average_score = sum((result.score / result.max_score * 100) for result in results) / results.count()
        average_score = round(average_score, 1)
    else:
        average_score = 0
    
    # Get pending assignments count
    assignments_count = StudentAssignment.objects.filter(student=student, is_submitted=False).count()
    
    context = {
        'school': school,
        'student': student,
        'recent_scores': recent_scores,
        'subject_count': subject_count,
        'average_score': average_score,
        'assignments_count': assignments_count,
    }
    return render(request, 'academic/student_dashboard.html', context)


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
def student_results_admin(request, student_id):
    """Admin view for viewing any student's results"""
    if request.user.user_type not in ['senior_admin', 'junior_admin']:
        messages.error(request, "You don't have permission to view other students' results.")
        return redirect('core:homepage')
    
    student = get_object_or_404(Student, id=student_id)
    school = student.school
    
    # Get all results for this student - using Result model
    results = Result.objects.filter(student=student).select_related('subject', 'recorded_by__user').order_by('-date_taken')
    
    # Filter options
    subject_id = request.GET.get('subject_id')
    exam_type = request.GET.get('exam_type')
    
    if subject_id:
        results = results.filter(subject_id=subject_id)
    
    if exam_type:
        results = results.filter(exam_type=exam_type)
    
    # Get unique subjects for filter dropdown
    subjects = Subject.objects.filter(result__student=student).distinct()
    
    # Calculate statistics
    total_results = results.count()
    if total_results > 0:
        average_percentage = sum((result.score / result.max_score * 100) for result in results) / total_results
    else:
        average_percentage = 0
    
    context = {
        'school': school,
        'student': student,
        'scores': results,  # Still call it 'scores' in template for consistency
        'subjects': subjects,
        'selected_subject_id': subject_id,
        'selected_exam_type': exam_type,
        'total_scores': total_results,
        'average_percentage': round(average_percentage, 1),
        'is_admin_view': True,
    }
    return render(request, 'academic/student_results.html', context)


@login_required
def admin_student_results(request, student_id):
    """View for admin to see any student's results"""
    if not hasattr(request.user, 'schooladmin') and not hasattr(request.user, 'junioradmin'):
        messages.error(request, "Access denied.")
        return redirect('core:homepage')
    
    student = get_object_or_404(Student, id=student_id)
    
    # Get all results for this student
    results = Result.objects.filter(student=student).select_related('subject', 'recorded_by__user').order_by('-date_taken')
    
    # Filter options
    subject_id = request.GET.get('subject_id')
    exam_type = request.GET.get('exam_type')
    
    if subject_id:
        results = results.filter(subject_id=subject_id)
    
    if exam_type:
        results = results.filter(exam_type=exam_type)
    
    # Get unique subjects for filter dropdown
    subjects = Subject.objects.filter(result__student=student).distinct()
    
    # Calculate statistics
    total_results = results.count()
    if total_results > 0:
        average_percentage = sum((result.score / result.max_score * 100) for result in results) / total_results
    else:
        average_percentage = 0
    
    context = {
        'school': school,
        'student': student,
        'scores': results,  # Still call it 'scores' in template
        'subjects': subjects,
        'selected_subject_id': subject_id,
        'selected_exam_type': exam_type,
        'total_scores': total_results,
        'average_percentage': round(average_percentage, 1),
        'is_admin_view': False,
    }
    return render(request, 'academic/student_results.html', context)

@login_required
def student_results(request):
    """View for students to see their own results"""
    if not hasattr(request.user, 'student'):
        messages.error(request, "You must be a student to view results.")
        return redirect('core:homepage')
    
    student = request.user.student
    school = student.school
    
    # Get all results for this student - using Result model
    results = Result.objects.filter(student=student).select_related('subject', 'recorded_by__user').order_by('-date_taken')
    
    # Filter options
    subject_id = request.GET.get('subject_id')
    exam_type = request.GET.get('exam_type')
    
    if subject_id:
        results = results.filter(subject_id=subject_id)
    
    if exam_type:
        results = results.filter(exam_type=exam_type)
    
    # Get unique subjects for filter dropdown
    subjects = Subject.objects.filter(result__student=student).distinct()
    
    # Calculate statistics
    total_results = results.count()
    if total_results > 0:
        average_percentage = sum((result.score / result.max_score * 100) for result in results) / total_results
    else:
        average_percentage = 0
    
    context = {
        'school': school,
        'student': student,
        'scores': results,  # Still call it 'scores' in template
        'subjects': subjects,
        'selected_subject_id': subject_id,
        'selected_exam_type': exam_type,
        'total_scores': total_results,
        'average_percentage': round(average_percentage, 1),
        'is_admin_view': False,
    }
    return render(request, 'academic/student_results.html', context)

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

# academic/views.py
@login_required
def assignment_detail(request, assignment_id):
    try:
        assignment = get_object_or_404(Assignment, id=assignment_id)
        student_assignment = get_object_or_404(
            StudentAssignment, 
            assignment=assignment, 
            student__user=request.user
        )
        
        return render(request, 'academic/assignment_detail.html', {
            'assignment': assignment,
            'student_assignment': student_assignment,
            'now': timezone.now()
        })
    except Exception as e:
        messages.error(request, f"Error loading assignment: {str(e)}")
        return redirect('academic:student_assignments')
    

@login_required
def subject_results_spreadsheet(request):
    """Main view for the subject results spreadsheet"""
    teacher = get_object_or_404(Teacher, user=request.user)
    school = teacher.school
    
    # Get teacher's classes and subjects
    classes = ClassLevel.objects.filter(
        classsubject__teacher=teacher,
        school=school
    ).distinct()
    
    teacher_subjects = Subject.objects.filter(
        classsubject__teacher=teacher
    ).distinct()
    
    # Generate session years
    current_year = timezone.now().year
    session_years = range(current_year - 5, current_year + 1)
    
    context = {
        'school': school,
        'classes': classes,
        'teacher_subjects': teacher_subjects,
        'session_years': reversed(list(session_years)),
    }
    return render(request, 'academic/subject_results_spreadsheet.html', context)

@login_required
def api_load_existing_scores(request):
    """API to load existing scores for a subject-class-term combination"""
    teacher = request.user.teacher
    subject_id = request.GET.get('subject_id')
    class_id = request.GET.get('class_id')
    term = request.GET.get('term')
    
    try:
        subject = get_object_or_404(Subject, id=subject_id)
        class_level = get_object_or_404(ClassLevel, id=class_id)
        
        # Get students in this class
        students = Student.objects.filter(class_level=class_level)
        
        # Build scores data
        scores_data = []
        for student in students:
            # Get all results for this student, subject, and term pattern
            results = Result.objects.filter(
                student=student,
                subject=subject,
                exam_type__startswith=f"term{term}_",
                recorded_by=teacher
            )
            
            for result in results:
                # Extract CA name from exam_type (e.g., "term1_test1" -> "test1")
                ca_name = result.exam_type.replace(f"term{term}_", "")
                if ca_name != "overall":  # Skip overall results
                    scores_data.append({
                        'student_id': student.id,
                        'ca_name': ca_name,
                        'score': result.score,
                        'comment': result.comment or ''
                    })
        
        return JsonResponse({
            'success': True,
            'scores': scores_data,
            'total_scores': len(scores_data)
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })

@login_required
def api_subject_students(request, subject_id):
    """API endpoint to get students for a specific subject"""
    teacher = get_object_or_404(Teacher, user=request.user)
    subject = get_object_or_404(Subject, id=subject_id)
    
    # Get classes where this teacher teaches this subject
    classes = ClassLevel.objects.filter(
        classsubject__teacher=teacher,
        classsubject__subject=subject
    ).distinct()
    
    # Get all students from those classes
    students = Student.objects.filter(
        class_level__in=classes,
        school=teacher.school
    ).select_related('user', 'class_level').order_by('user__first_name')
    
    students_data = []
    for student in students:
        students_data.append({
            'id': student.id,
            'full_name': student.user.get_full_name(),
            'admission_number': getattr(student, 'admission_number', ''),
            'class_name': student.class_level.name,
        })
    
    return JsonResponse({
        'students': students_data,
        'total_students': len(students_data),
        'classes': [cls.name for cls in classes]
    })


@login_required
def save_spreadsheet_results(request):
    """Save spreadsheet results to database"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            teacher = request.user.teacher
            
            class_id = data.get('class_id')
            subject_id = data.get('subject_id')
            term = data.get('term')
            session = data.get('session')
            ca_categories = data.get('ca_categories', [])
            results = data.get('results', [])
            
            print(f"=== SAVING SPREADSHEET RESULTS ===")
            print(f"Class: {class_id}, Subject: {subject_id}, Term: {term}")
            print(f"CA Categories: {len(ca_categories)}")
            print(f"Results to save: {len(results)}")
            
            subject = get_object_or_404(Subject, id=subject_id)
            class_level = get_object_or_404(ClassLevel, id=class_id)
            
            # Validate that teacher teaches this subject in this class
            if not ClassSubject.objects.filter(
                class_level=class_level,
                subject=subject,
                teacher=teacher
            ).exists():
                return JsonResponse({
                    'success': False,
                    'error': 'You do not teach this subject in the selected class'
                })
            
            saved_count = 0
            errors = []
            
            for result_data in results:
                student_id = result_data.get('student_id')
                ca_scores = result_data.get('ca_scores', [])
                comment = result_data.get('comment', '')
                total_score = result_data.get('total_score', 0)
                position = result_data.get('position', '')
                
                try:
                    student = get_object_or_404(Student, id=student_id, class_level=class_level)
                    
                    # Save individual CA scores as Result objects
                    for ca_score in ca_scores:
                        ca_name = ca_score.get('ca_name')
                        score = ca_score.get('score', 0)
                        max_score = ca_score.get('max_score', 0)
                        
                        # Create a unique exam type for this CA
                        exam_type = f"term{term}_{ca_name.lower().replace(' ', '_')}"
                        
                        # Create or update result
                        result, created = Result.objects.update_or_create(
                            student=student,
                            subject=subject,
                            exam_type=exam_type,
                            recorded_by=teacher,
                            defaults={
                                'score': score,
                                'max_score': max_score,
                                'comment': comment,
                                'date_taken': timezone.now().date(),
                            }
                        )
                        saved_count += 1
                        print(f"Saved {ca_name} for {student.user.get_full_name()}: {score}/{max_score}")
                    
                    # Save overall result
                    overall_result, created = Result.objects.update_or_create(
                        student=student,
                        subject=subject,
                        exam_type=f"term{term}_overall",
                        recorded_by=teacher,
                        defaults={
                            'score': total_score,
                            'max_score': 100,
                            'comment': f"Position: {position}. {comment}",
                            'date_taken': timezone.now().date(),
                        }
                    )
                    saved_count += 1
                    
                except Exception as e:
                    errors.append(f"Error saving student {student_id}: {str(e)}")
                    print(f"Error saving student {student_id}: {str(e)}")
            
            print(f"Successfully saved {saved_count} results")
            
            if errors:
                return JsonResponse({
                    'success': True,
                    'message': f'Saved {saved_count} results with some errors',
                    'saved_count': saved_count,
                    'errors': errors[:5]  # Return first 5 errors
                })
            else:
                return JsonResponse({
                    'success': True,
                    'message': f'Successfully saved {saved_count} results',
                    'saved_count': saved_count
                })
            
        except Exception as e:
            print(f"General error: {str(e)}")
            import traceback
            print(traceback.format_exc())
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500)
    
    return JsonResponse({'error': 'Method not allowed'}, status=405)