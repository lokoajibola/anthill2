from django.core.management.base import BaseCommand
from academic.models import Subject

class Command(BaseCommand):
    help = 'Create global subjects for all schools'

    def handle(self, *args, **options):
        subjects_data = [
            # Core Subjects
            {'code': 'ENG', 'name': 'English Language', 'category': 'Core'},
            {'code': 'MTH', 'name': 'Mathematics', 'category': 'Core'},
            {'code': 'SCI', 'name': 'Basic Science', 'category': 'Core'},
            {'code': 'SST', 'name': 'Social Studies', 'category': 'Core'},
            
            # Sciences
            {'code': 'PHY', 'name': 'Physics', 'category': 'Science'},
            {'code': 'CHEM', 'name': 'Chemistry', 'category': 'Science'},
            {'code': 'BIO', 'name': 'Biology', 'category': 'Science'},
            {'code': 'COMP', 'name': 'Computer Science', 'category': 'Science'},
            
            # Humanities
            {'code': 'GEO', 'name': 'Geography', 'category': 'Humanities'},
            {'code': 'HIS', 'name': 'History', 'category': 'Humanities'},
            {'code': 'GOV', 'name': 'Government', 'category': 'Humanities'},
            {'code': 'ECO', 'name': 'Economics', 'category': 'Humanities'},
            
            # Business & Commerce
            {'code': 'ACC', 'name': 'Accounting', 'category': 'Business'},
            {'code': 'BST', 'name': 'Business Studies', 'category': 'Business'},
            {'code': 'COMM', 'name': 'Commerce', 'category': 'Business'},
            
            # Languages
            {'code': 'FRN', 'name': 'French', 'category': 'Languages'},
            {'code': 'ARB', 'name': 'Arabic', 'category': 'Languages'},
            {'code': 'YOR', 'name': 'Yoruba', 'category': 'Languages'},
            {'code': 'IGB', 'name': 'Igbo', 'category': 'Languages'},
            {'code': 'HAU', 'name': 'Hausa', 'category': 'Languages'},
            
            # Arts & Creative
            {'code': 'MUS', 'name': 'Music', 'category': 'Arts'},
            {'code': 'ART', 'name': 'Fine Arts', 'category': 'Arts'},
            {'code': 'DRAMA', 'name': 'Drama', 'category': 'Arts'},
            {'code': 'LIT', 'name': 'Literature in English', 'category': 'Arts'},
            
            # Religious Studies
            {'code': 'CRK', 'name': 'Christian Religious Knowledge', 'category': 'Religious'},
            {'code': 'IRS', 'name': 'Islamic Religious Studies', 'category': 'Religious'},
            
            # Technical & Vocational
            {'code': 'AGRIC', 'name': 'Agricultural Science', 'category': 'Technical'},
            {'code': 'TECH', 'name': 'Technical Drawing', 'category': 'Technical'},
            {'code': 'HOME', 'name': 'Home Economics', 'category': 'Technical'},
            {'code': 'PHYED', 'name': 'Physical Education', 'category': 'Technical'},
        ]
        
        created_count = 0
        for data in subjects_data:
            subject, created = Subject.objects.get_or_create(
                code=data['code'],
                defaults={
                    'name': data['name'],
                    'category': data['category'],
                    'description': f"{data['name']} - {data['category']} subject"
                }
            )
            if created:
                created_count += 1
                self.stdout.write(f"Created subject: {data['name']}")
        
        self.stdout.write(
            self.style.SUCCESS(f'Successfully created {created_count} global subjects!')
        )