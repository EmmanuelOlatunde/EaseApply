"""
Base test classes and utilities for Analysis app tests.
Provides common setup, factories, and assertion helpers.
"""

from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework.authtoken.models import Token
from unittest.mock import patch
import time
import uuid
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework_simplejwt.tokens import AccessToken

from jobs.models import JobDescription
from resumes.models import Resume

User = get_user_model()


class TestDataFactory:
    """Factory class for creating test data."""
    
    @staticmethod
    def create_user(username="testuser", email="test@example.com", password="testpass123"):
        """Create a test user."""
        return User.objects.create_user(
            username=username,
            email=email,
            password=password
        )

    
    @staticmethod
    def create_job_description(user, **kwargs):
        """Create a test job description."""
        defaults = {
            'raw_content': 'Software Developer position at Test Company. Remote work available. Full-time position with salary range $60,000 - $80,000. Requirements: Python, Django, REST API development. Skills required: Python, Django, PostgreSQL. Experience level: Mid-level.',
            'title': 'Software Developer',
            'company': 'Test Company',
            'location': 'Remote',
            'job_type': 'full_time',
            'salary_range': '$60,000 - $80,000',
            'requirements': 'Python, Django, REST API development',
            'skills_required': 'Python, Django, PostgreSQL',
            'experience_level': 'Mid-level',
            'is_processed': True,
        }
        defaults.update(kwargs)
        return JobDescription.objects.create(user=user, **defaults)
    
    @staticmethod
    def create_resume_file():
        """Create a mock PDF file for resume upload."""
        # Create a simple PDF-like content
        content = b'%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n>>\nendobj\nxref\n0 2\n0000000000 65535 f \ntrailer\n<<\n/Size 2\n/Root 1 0 R\n>>\nstartxref\n9\n%%EOF'
        return SimpleUploadedFile(
            "test_resume.pdf",
            content,
            content_type="application/pdf"
        )
    
    @staticmethod
    def create_resume(user, **kwargs):
        """Create a test resume."""
        # Create a mock file if not provided
        if 'file' not in kwargs:
            kwargs['file'] = TestDataFactory.create_resume_file()
        
        defaults = {
            'original_filename': 'test_resume.pdf',
            'file_type': Resume.PDF,
            'file_size': 1024,
            # In test_base.py, line 104
            'extracted_text': 'Software developer with 6 years experience in Python and Django.',
            'full_name': 'John Doe',
            'contact_info': {
                'email': 'john@example.com',
                'phone': '+1234567890',
                'linkedin': 'https://linkedin.com/in/johndoe'
            },
            'skills': ['Python', 'Django', 'PostgreSQL', 'REST APIs'],
            'work_experience': [
                {
                    'company': 'Tech Company',
                    'position': 'Software Developer',
                    'duration': '2021-2024',
                    'description': 'Developed web applications using Django'
                }
            ],
            'education': [
                {
                    'institution': 'University of Technology',
                    'degree': 'BS Computer Science',
                    'year': '2021'
                }
            ],
            'certifications': ['AWS Certified Developer'],
            'projects': [
                {
                    'name': 'E-commerce Platform',
                    'description': 'Built using Django and PostgreSQL',
                    'technologies': ['Django', 'PostgreSQL', 'Redis']
                }
            ],
            'is_parsed': True,
        }
        defaults.update(kwargs)
        return Resume.objects.create(user=user, **defaults)
    
    @staticmethod
    def create_valid_resume(user, **kwargs):
        """Create a resume with valid extracted text."""
        defaults = {
            'extracted_text': 'Valid resume content with technical skills and experience. Software Engineer with 5 years of experience in Python, Django, and web development.'
        }
        defaults.update(kwargs)
        return TestDataFactory.create_resume(user, **defaults)
    
    @staticmethod
    def create_empty_resume(user, **kwargs):
        """Create a resume with empty extracted text."""
        defaults = {
            'extracted_text': '',
            'is_parsed': False,
        }
        defaults.update(kwargs)
        return TestDataFactory.create_resume(user, **defaults)
    
    @staticmethod
    def create_whitespace_resume(user, **kwargs):
        """Create a resume with only whitespace in extracted text."""
        defaults = {
            'extracted_text': '   \n\t   ',
            'is_parsed': False,
        }
        defaults.update(kwargs)
        return TestDataFactory.create_resume(user, **defaults)
    
    @staticmethod
    def create_unparsed_resume(user, **kwargs):
        """Create a resume that hasn't been parsed yet."""
        defaults = {
            'extracted_text': '',
            'is_parsed': False,
            'parsing_error': None,
        }
        defaults.update(kwargs)
        return TestDataFactory.create_resume(user, **defaults)
    
    @staticmethod
    def create_multiple_jobs(user, count=3):
        """Create multiple job descriptions for a user."""
        jobs = []
        for i in range(count):
            time.sleep(0.001)  # Ensure different timestamps
            job = TestDataFactory.create_job_description(
                user,
                title=f'Job {i+1}',
                company=f'Company {i+1}',
                raw_content=f'Job description {i+1} content with requirements and skills.'
            )
            jobs.append(job)
        return jobs
    
    @staticmethod
    def create_multiple_resumes(user, count=3):
        """Create multiple resumes for a user."""
        resumes = []
        for i in range(count):
            time.sleep(0.001)  # Ensure different timestamps
            resume = TestDataFactory.create_resume(
                user,
                original_filename=f'resume_{i+1}.pdf',
                full_name=f'User {i+1}',
                extracted_text=f'Resume {i+1} content with skills and experience.'
            )
            resumes.append(resume)
        return resumes


class MockServiceMixin:
    """Mixin providing mock service utilities."""
    
    def get_successful_service_response(self):
        """Get a successful AI service response."""
        return {
            'success': True,
            'cover_letter': 'Generated cover letter content for testing',
            'prompt_used': 'Test prompt used for generation',
            'metadata': {
                'model': 'test-model',
                'tokens_used': 500,
                'processing_time': 2.5,
                'template_type': 'professional'
            }
        }
    
    def get_failed_service_response(self, error="Service unavailable", error_type="service_error"):
        """Get a failed AI service response."""
        return {
            'success': False,
            'error': error,
            'error_type': error_type
        }
    
    def get_resume_analysis_response(self):
        """Get a successful resume analysis response."""
        return {
            'success': True,
            'analysis': 'Resume analysis content for testing',
            'score': 85,
            'strengths': ['Strong technical background', 'Relevant experience'],
            'improvements': ['Add more quantified achievements'],
            'prompt_used': 'Resume analysis prompt',
            'metadata': {
                'model': 'test-model',
                'tokens_used': 300,
                'processing_time': 1.8
            }
        }
    
    def get_job_match_response(self):
        """Get a successful job match response."""
        return {
            'success': True,
            'match_score': 78,
            'analysis': 'Job match analysis content for testing',
            'matching_skills': ['Python', 'Django'],
            'missing_skills': ['AWS', 'Docker'],
            'prompt_used': 'Job match analysis prompt',
            'metadata': {
                'model': 'test-model',
                'tokens_used': 400,
                'processing_time': 2.1
            }
        }
    
    def patch_openrouter_service(self, response=None):
        """Context manager to patch OpenRouter service."""
        if response is None:
            response = self.get_successful_service_response()
        
        return patch('analysis.services.OpenRouterService.generate_cover_letter', return_value=response)
    
    def patch_resume_analysis_service(self, response=None):
        """Context manager to patch resume analysis service."""
        if response is None:
            response = self.get_resume_analysis_response()
        
        return patch('analysis.services.OpenRouterService.analyze_resume', return_value=response)
    
    def patch_job_match_service(self, response=None):
        """Context manager to patch job match service."""
        if response is None:
            response = self.get_job_match_response()
        
        return patch('analysis.services.OpenRouterService.analyze_job_match', return_value=response)


class BaseAnalysisTestCase(APITestCase):
    """Base test case for Analysis app tests."""
    
    def setUp(self):
        """Set up test data."""
        # Create test users
        self.user = TestDataFactory.create_user(username="testuser")
        self.other_user = TestDataFactory.create_user(username="otheruser", email="other@example.com")
        
        # Create authentication tokens
        #self.token = Token.objects.create(user=self.user)
        self.token = AccessToken.for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {str(self.token)}')
       # self.other_token = Token.objects.create(user=self.other_user)
        self.other_token = AccessToken.for_user(self.other_user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {str(self.other_token)}')
        # Set up API URLs
        self.cover_letter_url = reverse('analysis:generate-cover-letter')
        #self.resume_analysis_url = reverse('analysis:analyze-resume')
        #self.job_match_url = reverse('analysis:job-match')
        self.url = self.cover_letter_url  # Alias for compatibility
        
        # Create test data
        self.job_description = TestDataFactory.create_job_description(self.user)
        self.resume = TestDataFactory.create_resume(self.user)
        
        # Authenticate by default
        self.authenticate()
    
    def authenticate(self, user=None):
        """Authenticate a user for API requests."""
        if user is None:
            user = self.user
        
        # Make sure token exists for the user
        token, created = Token.objects.get_or_create(user=user)
        
        # Set the authorization header
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {token.key}')
    
    def unauthenticate(self):
        """Remove authentication credentials."""
        self.client.credentials()
    
    def assert_successful_response(self, response, expected_status=200):
        """Assert that response is successful with expected status."""
        self.assertEqual(response.status_code, expected_status)
        self.assertTrue(response.data.get('success', False))
    
    def assert_error_response(self, response, expected_status=400, expected_success=False):
        """Assert that response is an error with expected status."""
        self.assertEqual(response.status_code, expected_status)
        self.assertEqual(response.data.get('success', True), expected_success)
    
    def create_job_description(self, user=None, **kwargs):
        """Helper to create job description."""
        if user is None:
            user = self.user
        return TestDataFactory.create_job_description(user, **kwargs)
    
    def create_resume(self, user=None, **kwargs):
        """Helper to create resume."""
        if user is None:
            user = self.user
        return TestDataFactory.create_resume(user, **kwargs)
    
    def get_valid_cover_letter_data(self, job_id=None, resume_id=None):
        return {
            'job_id': job_id or self.job_description.id,
            'resume_id': resume_id or self.resume.id,
            'template_type': 'professional'
        }


    def get_valid_resume_analysis_data(self, resume_id=None):
        """Get valid data for resume analysis."""
        return {
            'resume_id': resume_id or self.resume.id
        }
    
    def get_valid_job_match_data(self, job_id=None, resume_id=None):
        """Get valid data for job match analysis."""
        return {
            'job_description_id': job_id or self.job_description.id,
            'resume_id': resume_id or self.resume.id
        }


class AssertionHelpers:
    """Collection of custom assertion helpers for common test patterns."""
    
    @staticmethod
    def assert_model_created(test_case, model_class, expected_count=1, **filters):
        """Assert that a model instance was created with expected attributes."""
        actual_count = model_class.objects.filter(**filters).count()
        test_case.assertEqual(
            actual_count, 
            expected_count,
            f"Expected {expected_count} {model_class.__name__} instances, got {actual_count}"
        )
    
    @staticmethod
    def assert_response_contains_fields(test_case, response_data, required_fields):
        """Assert that response contains all required fields."""
        for field in required_fields:
            test_case.assertIn(
                field, 
                response_data, 
                f"Response missing required field: {field}"
            )
    
    @staticmethod
    def assert_timestamp_recent(test_case, timestamp_str, max_seconds_ago=10):
        """Assert that a timestamp is recent (within max_seconds_ago)."""
        from datetime import datetime, timezone
        timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
        now = datetime.now(timezone.utc)
        diff = (now - timestamp).total_seconds()
        test_case.assertLessEqual(
            diff, 
            max_seconds_ago,
            f"Timestamp {timestamp_str} is not recent enough"
        )
    
    @staticmethod
    def assert_analysis_result_created(test_case, user, analysis_type, expected_count=1):
        """Assert that an AnalysisResult was created with correct attributes."""
        from analysis.models import AnalysisResult
        results = AnalysisResult.objects.filter(user=user, analysis_type=analysis_type)
        test_case.assertEqual(
            results.count(),
            expected_count,
            f"Expected {expected_count} {analysis_type} AnalysisResult, got {results.count()}"
        )
        return results.first() if expected_count == 1 else results
    
    @staticmethod
    def assert_valid_uuid(test_case, uuid_string):
        """Assert that a string is a valid UUID."""
        try:
            uuid.UUID(uuid_string)
        except (ValueError, TypeError):
            test_case.fail(f"'{uuid_string}' is not a valid UUID")
    
    @staticmethod
    def assert_json_field_structure(test_case, json_data, expected_keys):
        """Assert that JSON field has expected structure."""
        if not isinstance(json_data, dict):
            test_case.fail(f"Expected dict, got {type(json_data)}")
        
        for key in expected_keys:
            test_case.assertIn(key, json_data, f"Missing key '{key}' in JSON data")


class DatabaseTestMixin:
    """Mixin providing database testing utilities."""
    
    def assert_database_count(self, model_class, expected_count):
        """Assert the total count of model instances in database."""
        actual_count = model_class.objects.count()
        self.assertEqual(
            actual_count,
            expected_count,
            f"Expected {expected_count} {model_class.__name__} instances, got {actual_count}"
        )
    
    def refresh_from_db(self, *instances):
        """Refresh multiple instances from database."""
        for instance in instances:
            instance.refresh_from_db()
        return instances[0] if len(instances) == 1 else instances
    
class ResumeTestMixin:
    """Mixin providing resume-specific test utilities."""
    
    def create_pdf_content(self):
        """Create mock PDF content for testing."""
        return b'%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n>>\nendobj\nxref\n0 2\n0000000000 65535 f \ntrailer\n<<\n/Size 2\n/Root 1 0 R\n>>\nstartxref\n9\n%%EOF'
    
    def create_docx_content(self):
        """Create mock DOCX content for testing."""
        # This is a minimal DOCX file structure
        return b'PK\x03\x04' + b'\x00' * 100  # Simplified DOCX header
    
    def assert_resume_parsed_correctly(self, resume):
        """Assert that resume was parsed correctly."""
        self.assertTrue(resume.is_parsed)
        self.assertIsNone(resume.parsing_error)
        self.assertIsNotNone(resume.parsed_at)
        
    def assert_resume_has_required_fields(self, resume):
        """Assert that resume has all required fields."""
        required_fields = ['user', 'file', 'original_filename', 'file_type', 'file_size']
        for field in required_fields:
            self.assertIsNotNone(getattr(resume, field))