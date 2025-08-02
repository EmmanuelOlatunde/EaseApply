"""
Business logic tests for the resume application
"""
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import AccessToken
from django.urls import reverse
from ..models import Resume
from ..serializers import ResumeAnalyticsSerializer

User = get_user_model()


class ResumeBusinessLogicTestCase(TestCase):
    """Test business logic and calculated fields"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='bizuser',
            email='biz@example.com',
            password='testpass123'
        )
    
    def test_contact_info_properties(self):
        """Test contact info property methods"""
        resume = Resume.objects.create(
            user=self.user,
            original_filename='contact_test.pdf',
            file_type=Resume.PDF,
            file_size=1024,
            contact_info={
                'email': 'test@example.com',
                'phone': '(555) 123-4567',
                'linkedin': 'https://linkedin.com/in/testuser'
            }
        )
        
        self.assertEqual(resume.contact_email, 'test@example.com')
        self.assertEqual(resume.contact_phone, '(555) 123-4567')
        self.assertEqual(resume.contact_linkedin, 'https://linkedin.com/in/testuser')
    
    def test_contact_info_properties_empty(self):
        """Test contact info properties when data is empty"""
        resume = Resume.objects.create(
            user=self.user,
            original_filename='empty_contact.pdf',
            file_type=Resume.PDF,
            file_size=1024,
            contact_info={}
        )
        
        self.assertIsNone(resume.contact_email)
        self.assertIsNone(resume.contact_phone)
        self.assertIsNone(resume.contact_linkedin)
        
        # Test with None contact_info
        resume.contact_info = None
        self.assertIsNone(resume.contact_email)
    
    def test_skills_display_method(self):
        """Test skills display formatting"""
        resume = Resume.objects.create(
            user=self.user,
            original_filename='skills_test.pdf',
            file_type=Resume.PDF,
            file_size=1024,
            skills=['Python', 'Django', 'JavaScript', 'React', 'PostgreSQL']
        )
        
        skills_display = resume.get_skills_display()
        self.assertEqual(skills_display, 'Python, Django, JavaScript, React, PostgreSQL')
        
        # Test with empty skills
        resume.skills = []
        self.assertEqual(resume.get_skills_display(), '')
        
        # Test with None skills
        resume.skills = None
        self.assertEqual(resume.get_skills_display(), '')
    
    def test_certifications_display_method(self):
        """Test certifications display formatting"""
        resume = Resume.objects.create(
            user=self.user,
            original_filename='certs_test.pdf',
            file_type=Resume.PDF,
            file_size=1024,
            certifications=['AWS Certified', 'Kubernetes Administrator', 'Scrum Master']
        )
        
        certs_display = resume.get_certifications_display()
        self.assertEqual(certs_display, 'AWS Certified, Kubernetes Administrator, Scrum Master')
    
    def test_resume_parsing_workflow(self):
        """Test the complete parsing workflow business logic"""
        resume = Resume.objects.create(
            user=self.user,
            original_filename='workflow_test.pdf',
            file_type=Resume.PDF,
            file_size=1024,
            extracted_text='Test content'
        )
        
        # Initially should not be parsed
        self.assertFalse(resume.is_parsed)
        self.assertIsNone(resume.parsed_at)
        
        # Simulate successful parsing
        resume.full_name = 'John Doe'
        resume.summary = 'Software Engineer'
        resume.skills = ['Python', 'Django']
        resume.is_parsed = True
        resume.parsed_at = timezone.now()
        resume.save()
        
        # Verify parsing status
        self.assertTrue(resume.is_parsed)
        self.assertIsNotNone(resume.parsed_at)
        self.assertEqual(resume.full_name, 'John Doe')
    
    def test_file_auto_detection_logic(self):
        """Test automatic file type and size detection"""
        from django.core.files.uploadedfile import SimpleUploadedFile
        
        pdf_file = SimpleUploadedFile(
            "auto_detect.pdf",
            b'%PDF-1.4 fake content',
            content_type="application/pdf"
        )
        
        resume = Resume(
            user=self.user,
            file=pdf_file
        )
        resume.save()
        
        # Should auto-detect file type and set filename
        self.assertEqual(resume.file_type, Resume.PDF)
        self.assertEqual(resume.original_filename, 'auto_detect.pdf')
        self.assertEqual(resume.file_size, len(b'%PDF-1.4 fake content'))
    
    def test_resume_analytics_calculations(self):
        """Test analytics calculations"""
        # Create resume with comprehensive data
        resume = Resume.objects.create(
            user=self.user,
            original_filename='analytics_test.pdf',
            file_type=Resume.PDF,
            file_size=1024,
            full_name='Analytics User',
            summary='Test summary',
            contact_info={'email': 'analytics@test.com', 'phone': '555-1234'},
            skills=['Python', 'Django', 'JavaScript'],
            work_experience=[
                {'title': 'Developer', 'company': 'Tech Corp', 'duration': '2020-2023'}
            ],
            education=[
                {'degree': 'BS Computer Science', 'institution': 'Tech University', 'year': '2018'}
            ],
            certifications=['AWS Certified'],
            projects=[
                {'name': 'Test Project', 'description': ['Built web app']}
            ],
            is_parsed=True
        )
        
        serializer = ResumeAnalyticsSerializer(resume)
        data = serializer.data
        
        self.assertEqual(data['total_skills'], 3)
        self.assertEqual(data['total_experience_entries'], 1)
        self.assertEqual(data['total_education_entries'], 1)
        self.assertEqual(data['total_certifications'], 1)
        self.assertEqual(data['total_projects'], 1)
        self.assertTrue(data['has_contact_info'])
        self.assertEqual(data['completion_score'], 100.0)  # All sections filled
    
    def test_completion_score_calculation(self):
        """Test completion score calculation with partial data"""
        # Resume with only some sections
        resume = Resume.objects.create(
            user=self.user,
            original_filename='partial_test.pdf',
            file_type=Resume.PDF,
            file_size=1024,
            full_name='Partial User',
            contact_info={'email': 'partial@test.com'},
            skills=['Python'],
            is_parsed=True
        )
        
        serializer = ResumeAnalyticsSerializer(resume)
        data = serializer.data
        
        # Should have partial completion score
        # 3 sections out of 8: name, contact, skills = 37.5%
        self.assertEqual(data['completion_score'], 37.5)
        
        # Unparsed resume should have 0 completion
        unparsed_resume = Resume.objects.create(
            user=self.user,
            original_filename='unparsed.pdf',
            file_type=Resume.PDF,
            file_size=1024,
            is_parsed=False
        )
        
        unparsed_serializer = ResumeAnalyticsSerializer(unparsed_resume)
        unparsed_data = unparsed_serializer.data
        self.assertEqual(unparsed_data['completion_score'], 0)


class ResumeSearchFilterTestCase(APITestCase):
    """Test search and filtering functionality"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='searchuser',
            email='search@example.com',
            password='testpass123'
        )
        self.jwt_token = AccessToken.for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {str(self.jwt_token)}')
        
        # Create test resumes with different attributes
        self.resume1 = Resume.objects.create(
            user=self.user,
            original_filename='python_developer_resume.pdf',
            file_type=Resume.PDF,
            file_size=1024,
            full_name='Python Developer',
            skills=['Python', 'Django', 'PostgreSQL'],
            is_parsed=True
        )
        
        self.resume2 = Resume.objects.create(
            user=self.user,
            original_filename='javascript_engineer.pdf',
            file_type=Resume.PDF,
            file_size=2048,
            full_name='JavaScript Engineer',
            skills=['JavaScript', 'React', 'Node.js'],
            is_parsed=True
        )
        
        self.resume3 = Resume.objects.create(
            user=self.user,
            original_filename='unparsed_resume.pdf',
            file_type=Resume.PDF,
            file_size=1536,
            full_name='Unparsed User',
            is_parsed=False
        )
    
    def test_search_by_filename(self):
        """Test searching resumes by filename"""
        url = reverse('resumes:resume-list-create')
        response = self.client.get(url, {'search': 'python'})
        
        self.assertEqual(response.status_code, 200)
        results = response.data['results']
        
        # Should find the python developer resume
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['original_filename'], 'python_developer_resume.pdf')
    
    def test_search_by_full_name(self):
        """Test searching resumes by full name"""
        url = reverse('resumes:resume-list-create')
        response = self.client.get(url, {'search': 'JavaScript'})
        
        self.assertEqual(response.status_code, 200)
        results = response.data['results']
        
        # Should find the JavaScript engineer resume
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['full_name'], 'JavaScript Engineer')
    
    def test_filter_by_parsed_status(self):
        """Test filtering resumes by parsing status"""
        url = reverse('resumes:resume-list-create')
        
        # Filter for parsed resumes only
        response = self.client.get(url, {'parsed': 'true'})
        self.assertEqual(response.status_code, 200)
        results = response.data['results']
        
        # Should return only parsed resumes
        self.assertEqual(len(results), 2)
        for resume in results:
            self.assertTrue(resume['is_parsed'])
        
        # Filter for unparsed resumes only
        response = self.client.get(url, {'parsed': 'false'})
        self.assertEqual(response.status_code, 200)
        results = response.data['results']
        
        # Should return only unparsed resumes
        self.assertEqual(len(results), 1)
        self.assertFalse(results[0]['is_parsed'])
    
    def test_case_insensitive_search(self):
        """Test that search is case insensitive"""
        url = reverse('resumes:resume-list-create')
        
        # Search with different cases
        test_queries = ['PYTHON', 'Python', 'python', 'PyThOn']
        
        for query in test_queries:
            with self.subTest(query=query):
                response = self.client.get(url, {'search': query})
                self.assertEqual(response.status_code, 200)
                results = response.data['results']
                self.assertEqual(len(results), 1)
                self.assertEqual(results[0]['original_filename'], 'python_developer_resume.pdf')
    
    def test_empty_search_results(self):
        """Test search with no matching results"""
        url = reverse('resumes:resume-list-create')
        response = self.client.get(url, {'search': 'nonexistent'})
        
        self.assertEqual(response.status_code, 200)
        results = response.data['results']
        self.assertEqual(len(results), 0)
    
    def test_combined_filters(self):
        """Test combining search and filter parameters"""
        url = reverse('resumes:resume-list-create')
        response = self.client.get(url, {'search': 'developer', 'parsed': 'true'})
        
        self.assertEqual(response.status_code, 200)
        results = response.data['results']
        
        # Should find parsed resumes matching the search
        self.assertEqual(len(results), 1)
        self.assertTrue(results[0]['is_parsed'])
        self.assertIn('developer', results[0]['original_filename'].lower())
