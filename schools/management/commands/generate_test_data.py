import os
import random
from django.core.management.base import BaseCommand
from django.contrib.auth.hashers import make_password
from django.utils import timezone
from datetime import timedelta
import pandas as pd
from schools.models import School, SchoolAdmin, Subscription, Payment
from users.models import User, Teacher, Student
from academic.models import Subject, ClassLevel, Assignment, StudentAssignment, Result

class Command(BaseCommand):
    help = 'Generate comprehensive test data for Anthill system'

    def handle(self, *args, **options):
        self.stdout.write('Generating test data...')
        
        # Clear existing data (optional - be careful in production!)
        self.clear_existing_data()
        
        # Create schools
        schools = self.create_schools()
        
        # Create class levels for each school
        class_levels_by_school = {}
        for school in schools:
            class_levels = self.create_class_levels(school)
            class_levels_by_school[school.id] = class_levels
        
        # Create subjects for each school
        subjects_by_school = {}
        # for school in schools:
        #     subjects = self.create_subjects(school)
        #     subjects_by_school[school.id] = subjects
        
        # Create users for each school
        login_data = []
        for school in schools:
            school_data = self.create_school_users(
                school, 
                class_levels_by_school[school.id],
                # subjects_by_school[school.id]
            )
            login_data.extend(school_data)
        
        # Create subscriptions and payments
        self.create_subscriptions_and_payments(schools)
        
        # Create academic data
        self.create_academic_data(schools, subjects_by_school)
        
        # Export login credentials to Excel
        self.export_login_data(login_data)
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully generated test data for {len(schools)} schools! '
                f'Login credentials exported to test_data_logins.xlsx'
            )
        )

    def create_schools(self):
        schools_data = [
            {
                'name': 'Greenwood International School',
                'type': 'secondary',
                'subscription': 'pro',
                'phone': '+2348012345001',
                'email': 'admin@greenwood.edu.ng',
                'address': '1 Education Road, GRA, Ikeja, Lagos',
                'motto': 'Excellence in Education',
                'vision': 'To be the leading educational institution in West Africa',
                'mission': 'Providing quality education that transforms lives'
            },
            {
                'name': 'Sunrise Primary Academy',
                'type': 'primary', 
                'subscription': 'basic',
                'phone': '+2348012345002',
                'email': 'info@sunriseacademy.ng',
                'address': '25 Learning Street, Surulere, Lagos',
                'motto': 'Nurturing Young Minds',
                'vision': 'Creating a foundation for lifelong learning',
                'mission': 'Inspiring curiosity and creativity in every child'
            },
            {
                'name': 'Royal Comprehensive College',
                'type': 'combined',
                'subscription': 'enterprise', 
                'phone': '+2348012345003',
                'email': 'contact@royalcollege.ng',
                'address': '48 College Avenue, Victoria Island, Lagos',
                'motto': 'Knowledge, Character, Excellence',
                'vision': 'Developing future leaders with global perspective',
                'mission': 'Holistic education for academic and personal growth'
            },
            {
                'name': 'Prestige High School',
                'type': 'secondary',
                'subscription': 'pro',
                'phone': '+2348012345004',
                'email': 'admin@prestigeschool.ng', 
                'address': '15 Prestige Road, Lekki Phase 1, Lagos',
                'motto': 'Striving for Greatness',
                'vision': 'Empowering students to achieve their full potential',
                'mission': 'Quality education with modern teaching methodologies'
            },
            {
                'name': 'Little Scholars Academy',
                'type': 'primary',
                'subscription': 'basic',
                'phone': '+2348012345005',
                'email': 'info@littlescholars.ng',
                'address': '8 Children Street, Yaba, Lagos', 
                'motto': 'Small Steps to Big Dreams',
                'vision': 'Creating a nurturing environment for early learning',
                'mission': 'Making learning fun and engaging for young children'
            },
            {
                'name': 'Metropolitan Secondary School',
                'type': 'secondary',
                'subscription': 'pro',
                'phone': '+2348012345006',
                'email': 'contact@metropolitanschool.ng',
                'address': '32 Urban Avenue, Apapa, Lagos',
                'motto': 'Education for Urban Excellence', 
                'vision': 'Preparing students for the challenges of modern society',
                'mission': 'Blending traditional values with contemporary education'
            },
            {
                'name': 'Heritage International School',
                'type': 'combined',
                'subscription': 'enterprise',
                'phone': '+2348012345007',
                'email': 'admin@heritageschool.ng',
                'address': '12 Legacy Road, Ikoyi, Lagos',
                'motto': 'Preserving Values, Embracing Innovation',
                'vision': 'Balancing cultural heritage with global education standards',
                'mission': 'Developing well-rounded individuals with strong moral character'
            },
            {
                'name': 'Future Leaders Academy',
                'type': 'secondary', 
                'subscription': 'pro',
                'phone': '+2348012345008',
                'email': 'info@futureleaders.ng',
                'address': '55 Progress Street, Ikeja, Lagos',
                'motto': 'Shaping Tomorrow\'s Leaders Today',
                'vision': 'Creating innovative leaders for the 21st century',
                'mission': 'Fostering leadership skills and entrepreneurial mindset'
            },
            {
                'name': 'Bright Stars Elementary',
                'type': 'primary',
                'subscription': 'basic',
                'phone': '+2348012345009', 
                'email': 'contact@brightstars.ng',
                'address': '27 Sunshine Road, Maryland, Lagos',
                'motto': 'Where Every Child Shines',
                'vision': 'Unlocking the potential in every young learner',
                'mission': 'Personalized attention for optimal development'
            },
            {
                'name': 'Elite Comprehensive College', 
                'type': 'combined',
                'subscription': 'enterprise',
                'phone': '+2348012345010',
                'email': 'admin@elitecollege.ng',
                'address': '42 Excellence Boulevard, VI, Lagos',
                'motto': 'The Pinnacle of Educational Excellence',
                'vision': 'Setting the standard for quality education in Africa',
                'mission': 'Comprehensive education with international benchmarks'
            }
        ]
        
        schools = []
        for data in schools_data:
            school = School.objects.create(
                name=data['name'],
                school_type=data['type'],
                subscription_type=data['subscription'],
                phone=data['phone'],
                email=data['email'],
                address=data['address'],
                motto=data['motto'],
                vision=data['vision'],
                mission=data['mission'],
                primary_color='#{:06x}'.format(random.randint(0, 0xFFFFFF))
            )
            schools.append(school)
            self.stdout.write(f"Created school: {school.name}")
        
        return schools

    def create_class_levels(self, school):
        if school.school_type == 'primary':
            levels = [
                ('Nursery 1', 1), ('Nursery 2', 2), ('Kindergarten 1', 3), 
                ('Kindergarten 2', 4), ('Primary 1', 5), ('Primary 2', 6),
                ('Primary 3', 7), ('Primary 4', 8), ('Primary 5', 9)
            ]
        elif school.school_type == 'secondary':
            levels = [
                ('JSS 1', 10), ('JSS 2', 11), ('JSS 3', 12),
                ('SS 1', 13), ('SS 2', 14), ('SS 3', 15)
            ]
        else:  # combined
            levels = [
                ('Primary 1', 1), ('Primary 2', 2), ('Primary 3', 3),
                ('Primary 4', 4), ('Primary 5', 5), ('JSS 1', 6),
                ('JSS 2', 7), ('JSS 3', 8), ('SS 1', 9), ('SS 2', 10), ('SS 3', 11)
            ]
        
        class_levels = []
        for name, level in levels:
            class_level = ClassLevel.objects.create(
                name=name,
                level=level,
                school=school
            )
            class_levels.append(class_level)
        
        return class_levels

    # def create_subjects(self, school):
        # Common subjects with school-specific codes
        common_subjects = [
            ('English Language', 'Language and communication skills'),
            ('Mathematics', 'Numeracy and problem solving'),
            ('Basic Science', 'Fundamental scientific principles'),
            ('Social Studies', 'Social sciences and citizenship'),
        ]
        
        if school.school_type in ['secondary', 'combined']:
            common_subjects.extend([
                ('Physics', 'Physical sciences and mechanics'),
                ('Chemistry', 'Chemical substances and reactions'),
                ('Biology', 'Living organisms and life processes'),
                ('Geography', 'Earth and environmental studies'),
                ('History', 'Historical events and civilizations'),
                ('Economics', 'Economic principles and systems'),
                ('Accounting', 'Financial recording and reporting'),
                ('Business Studies', 'Business principles and practices'),
                ('Christian Religious Knowledge', 'Biblical studies and ethics'),
                ('Islamic Studies', 'Islamic teachings and principles'),
                ('French', 'French language and culture'),
                ('Music', 'Musical theory and practice'),
                ('Fine Arts', 'Visual arts and creativity'),
            ])
        
        subjects = []
        for name, description in common_subjects:
            # Create truly unique code by including school ID
            school_id_part = str(school.id).zfill(2)
            subject_abbr = ''.join([word[0] for word in name.split()[:2]]).upper()
            code = f"{school_id_part}{subject_abbr}"
            
            subject = Subject.objects.create(
                name=name,
                code=code,
                school=school,
                description=f"{description} - {school.name}"
            )
            subjects.append(subject)
        
        return subjects

    def create_school_users(self, school, class_levels): #, subjects):
        login_data = []
        
        # Create senior admin
        senior_admin = User.objects.create_user(
            username=f"admin_{school.name.lower().replace(' ', '_')}",
            password='admin123',
            email=school.email,
            first_name='School',
            last_name='Administrator',
            user_type='senior_admin',
            phone=school.phone
        )
        
        SchoolAdmin.objects.create(
            school=school,
            user=senior_admin,
            is_senior=True
        )
        
        login_data.append({
            'school': school.name,
            'role': 'Senior Admin',
            'username': senior_admin.username,
            'password': 'admin123',
            'full_name': senior_admin.get_full_name(),
            'email': senior_admin.email
        })
        
        # Create 2-3 junior admins
        junior_admin_names = [
            ('David', 'Johnson'), ('Sarah', 'Williams'), ('Michael', 'Brown')
        ]
        for i, (first, last) in enumerate(junior_admin_names[:random.randint(2,3)]):
            junior_admin = User.objects.create_user(
                username=f"junior_{school.name.lower().replace(' ', '_')}_{i+1}",
                password='admin123',
                email=f"junior{i+1}@{school.email.split('@')[1]}",
                first_name=first,
                last_name=last,
                user_type='junior_admin',
                phone=f"+23480{random.randint(1000000, 9999999)}"
            )
            
            SchoolAdmin.objects.create(
                school=school,
                user=junior_admin,
                is_senior=False
            )
            
            login_data.append({
                'school': school.name,
                'role': 'Junior Admin',
                'username': junior_admin.username,
                'password': 'admin123',
                'full_name': junior_admin.get_full_name(),
                'email': junior_admin.email
            })
        
        # Create teachers (5-15 per school based on size)
        teacher_first_names = ['James', 'Mary', 'John', 'Patricia', 'Robert', 'Jennifer', 
                              'Michael', 'Linda', 'William', 'Elizabeth', 'David', 'Susan']
        teacher_last_names = ['Smith', 'Johnson', 'Williams', 'Jones', 'Brown', 'Davis', 
                             'Miller', 'Wilson', 'Moore', 'Taylor', 'Anderson', 'Thomas']
        
        num_teachers = random.randint(5, 15)
        teachers = []
        for i in range(num_teachers):
            first_name = random.choice(teacher_first_names)
            last_name = random.choice(teacher_last_names)
            
            teacher_user = User.objects.create_user(
                username=f"teacher_{school.name.lower().replace(' ', '_')}_{i+1}",
                password='teacher123',
                email=f"teacher{i+1}@{school.email.split('@')[1]}",
                first_name=first_name,
                last_name=last_name,
                user_type='teacher',
                phone=f"+23480{random.randint(1000000, 9999999)}"
            )
            
            teacher = Teacher.objects.create(
                user=teacher_user,
                school=school
            )
            
            # Assign 2-4 random subjects to teacher
            teacher_subjects = random.sample(subjects, random.randint(2, 4))
            teacher.subjects.set(teacher_subjects)
            teachers.append(teacher)
            
            login_data.append({
                'school': school.name,
                'role': 'Teacher',
                'username': teacher_user.username,
                'password': 'teacher123',
                'full_name': teacher_user.get_full_name(),
                'email': teacher_user.email,
                'subjects': ', '.join([s.name for s in teacher_subjects])
            })
        
        # Create students (20-100 per school based on subscription)
        student_first_names = ['Chiamaka', 'Adebola', 'Chukwuma', 'Folake', 'Emeka', 'Ngozi',
                              'Oluwatobi', 'Amina', 'Ibrahim', 'Fatima', 'Kemi', 'Segun',
                              'Bola', 'Tunde', 'Yemi', 'Funke', 'Kunle', 'Bimpe', 'Dayo', 'Sade']
        student_last_names = ['Adeyemi', 'Okafor', 'Mohammed', 'Eze', 'Ogunleye', 'Suleiman',
                             'Okoro', 'Bello', 'Adewale', 'Ibe', 'Oladipo', 'Yusuf', 'Obi',
                             'Balogun', 'Okonkwo', 'Jibril', 'Odunsi', 'Mustapha', 'Okafor', 'Ali']
        
        if school.subscription_type == 'basic':
            num_students = random.randint(20, 50)
        elif school.subscription_type == 'pro':
            num_students = random.randint(50, 80)
        else:  # enterprise
            num_students = random.randint(80, 100)
        
        for i in range(num_students):
            first_name = random.choice(student_first_names)
            last_name = random.choice(student_last_names)
            class_level = random.choice(class_levels)
            
            student_user = User.objects.create_user(
                username=f"student_{school.name.lower().replace(' ', '_')}_{i+1}",
                password='student123',
                email=f"student{i+1}@{school.email.split('@')[1]}",
                first_name=first_name,
                last_name=last_name,
                user_type='student',
                phone=f"+23480{random.randint(1000000, 9999999)}"
            )
            
            student = Student.objects.create(
                user=student_user,
                school=school,
                admission_number=f"{school.name[:3].upper()}{2024}{i+1:04d}",
                class_level=class_level
            )
            
            login_data.append({
                'school': school.name,
                'role': 'Student',
                'username': student_user.username,
                'password': 'student123',
                'full_name': student_user.get_full_name(),
                'email': student_user.email,
                'admission_number': student.admission_number,
                'class_level': class_level.name
            })
        
        return login_data

    def create_subscriptions_and_payments(self, schools):
        for school in schools:
            # Create subscription
            start_date = timezone.now().date() - timedelta(days=random.randint(30, 365))
            end_date = start_date + timedelta(days=365)
            
            Subscription.objects.create(
                school=school,
                start_date=start_date,
                end_date=end_date,
                is_active=True,
                auto_renew=random.choice([True, False])
            )
            
            # Create payment history
            payment_amounts = {
                'basic': 99, 'pro': 199, 'enterprise': 399
            }
            
            for i in range(random.randint(3, 12)):  # 3-12 months of payment history
                payment_date = start_date + timedelta(days=30 * i)
                if payment_date <= timezone.now().date():
                    Payment.objects.create(
                        school=school,
                        amount=payment_amounts[school.subscription_type],
                        due_date=payment_date + timedelta(days=30),
                        status=random.choice(['completed', 'completed', 'completed', 'pending']),
                        description=f"Monthly subscription - {payment_date.strftime('%B %Y')}"
                    )

    def create_academic_data(self, schools, subjects_by_school):
        for school in schools:
            teachers = Teacher.objects.filter(school=school)
            students = Student.objects.filter(school=school)
            subjects = subjects_by_school[school.id]
            
            # Create assignments
            for teacher in teachers:
                teacher_subjects = teacher.subjects.all()
                if teacher_subjects:
                    for subject in teacher_subjects[:2]:  # 2 assignments per subject
                        assignment = Assignment.objects.create(
                            title=f"{subject.name} Assignment {random.randint(1, 3)}",
                            description=f"Complete the following exercises from chapter {random.randint(1, 10)}. Submit by the due date.",
                            subject=subject,
                            teacher=teacher,
                            due_date=timezone.now() + timedelta(days=random.randint(7, 30)),
                            max_score=random.choice([20, 25, 30, 50, 100])
                        )
                        
                        # Create student assignments for upper class students
                        upper_class_students = students.filter(class_level__level__gte=5)
                        for student in upper_class_students:
                            StudentAssignment.objects.create(
                                assignment=assignment,
                                student=student
                            )
            
            # Create results
            for student in students:
                student_subjects = random.sample(list(subjects), min(len(subjects), random.randint(3, 8)))
                for subject in student_subjects:
                    for exam_type in ['test', 'assignment', 'exam']:
                        if random.random() > 0.3:  # 70% chance of having a result
                            teacher = random.choice(teachers)
                            Result.objects.create(
                                student=student,
                                subject=subject,
                                exam_type=exam_type,
                                score=random.randint(40, 95),
                                max_score=100,
                                date_taken=timezone.now().date() - timedelta(days=random.randint(1, 90)),
                                recorded_by=teacher
                            )

    def export_login_data(self, login_data):
        df = pd.DataFrame(login_data)
        
        # Reorder columns for better readability
        column_order = ['school', 'role', 'username', 'password', 'full_name', 'email']
        additional_columns = [col for col in df.columns if col not in column_order]
        df = df[column_order + additional_columns]
        
        # Export to Excel with different sheets for each role
        with pd.ExcelWriter('test_data_logins.xlsx') as writer:
            # All data in one sheet
            df.to_excel(writer, sheet_name='All_Users', index=False)
            
            # Separate sheets for each role
            for role in df['role'].unique():
                sheet_name = role.replace(' ', '_')[:31]  # Excel sheet name limit
                role_data = df[df['role'] == role]
                role_data.to_excel(writer, sheet_name=sheet_name, index=False)
        
        self.stdout.write(f"Login data exported to test_data_logins.xlsx")

    def clear_existing_data(self):
        """Optional: Clear existing test data (use with caution!)"""
        self.stdout.write("Clearing existing test data...")
        User.objects.filter(user_type__in=['senior_admin', 'junior_admin', 'teacher', 'student']).delete()
        School.objects.all().delete()
        Subject.objects.all().delete()
        ClassLevel.objects.all().delete()
        self.stdout.write("Existing test data cleared.")