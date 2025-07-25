import os
import tempfile
from unittest.mock import patch
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from jobs.models import JobDescription
from rest_framework_simplejwt.tokens import AccessToken #RefreshToken


User = get_user_model()


class BaseJobTestCase(APITestCase):
    """Base test case with common setup for all job description tests"""
    
    def setUp(self):
        """Set up test data"""
        # Create test users
        self.user1 = User.objects.create_user(
            username='testuser1',
            email='test1@example.com',
            password='testpass123'
        )
        self.user2 = User.objects.create_user(
            username='testuser2',
            email='test2@example.com',
            password='testpass123'
        )

        # Create API client & tokens
        self.client = APIClient()
        # self.token1 = Token.objects.create(user=self.user1)
        # self.token2 = Token.objects.create(user=self.user2)
        self.jwt_token1 = AccessToken.for_user(self.user1)
        self.jwt_token2 = AccessToken.for_user(self.user2)
        

        # Sample job content
        self.sample_job_content = """
        Software Engineer - Full Stack
        TechCorp Inc.
        Location: San Francisco, CA
        Salary: $100,000 - $120,000

        Requirements:
        - 3+ years of experience in web development
        - Proficiency in Python, Django, React
        - Bachelor's degree in Computer Science

        Skills Required:
        - Python, Django, React, PostgreSQL
        - Git, Docker, AWS
        """

        # Create job descriptions for testing
        self.job1 = JobDescription.objects.create(
            user=self.user1,
            raw_content=self.sample_job_content,
            title="Software Engineer",
            company="TechCorp Inc.",
            location="San Francisco, CA",
            job_type="full_time",
            salary_range="$100,000 - $120,000",
            is_processed=True
        )

        self.job2 = JobDescription.objects.create(
            user=self.user1,
            raw_content="Another job description",
            title="Data Scientist",
            company="DataCorp",
            is_processed=False
        )

        # Job belonging to user2
        self.job_user2 = JobDescription.objects.create(
            user=self.user2,
            raw_content="User2 job description",
            title="Backend Developer",
            company="BackendCorp"
        )

    def authenticate_user1(self):
        """Authenticate as user1"""
        #self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token1.key}')
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {str(self.jwt_token1)}')

    def authenticate_user2(self):
        """Authenticate as user2"""
        #self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token2.key}')
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {str(self.jwt_token2)}')

    def unauthenticate(self):
        """Remove authentication"""
        self.client.credentials()

    def create_test_file(self, filename, content, content_type='text/plain'):
        """Helper method to create test files"""
        return SimpleUploadedFile(
            filename,
            content.encode('utf-8') if isinstance(content, str) else content,
            content_type=content_type
        )


class JobDescriptionCreateViewTests(BaseJobTestCase):
    """Tests for JobDescriptionCreateView"""
    
    def setUp(self):
        super().setUp()
        self.url = reverse('jobs:job-create')  # Adjust URL name as needed
    
    def test_create_job_with_text_content_authenticated(self):
        """Test creating job description with text content"""
        self.authenticate_user1()
        data = {
            'raw_content': 'New job description content',
            'is_active': True
        }

        with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
            tmp_file.write(b'Test document content')
            tmp_file_path = tmp_file.name
        with open(tmp_file_path, 'rb') as f:
            test_file = SimpleUploadedFile('test_doc.txt', f.read())
            JobDescription.objects.create(
                user=self.user1,
                raw_content='Job with document',
                document=test_file
            )
        
        with patch('jobs.serializers.extract_job_details') as mock_extract:
            mock_extract.return_value = {
                'title': 'Test Job',
                'company': 'Test Company'
            }
            
            response = self.client.post(self.url, data, format='json')
        
        # Expect 201 Created
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Verify the new job exists
        self.assertTrue(JobDescription.objects.filter(
            user=self.user1,
            raw_content='New job description content',
            is_active=True
        ).exists())
        
        # Verify the mocked fields were applied
        new_job = JobDescription.objects.get(raw_content='New job description content')
        self.assertEqual(new_job.title, 'Test Job')
        self.assertEqual(new_job.company, 'Test Company')
        
        # Clean up temp file
        try:
            os.unlink(tmp_file_path)
        except FileNotFoundError:
            pass

class JobDescriptionViewsIntegrationTests(BaseJobTestCase):
    """Integration tests for job description views workflow"""
    
    def test_complete_job_lifecycle(self):
        """Test complete job lifecycle: create -> retrieve -> update -> reprocess -> delete"""
        self.authenticate_user1()
        
        # 1. Create job
        create_url = reverse('jobs:job-create')
        create_data = {
            'raw_content': 'Full stack developer position at StartupCorp'
        }
        
        with patch('jobs.serializers.extract_job_details') as mock_extract:
            mock_extract.return_value = {
                'title': 'Full Stack Developer',
                'company': 'StartupCorp'
            }
            
            create_response = self.client.post(create_url, create_data, format='json')
        
        self.assertEqual(create_response.status_code, status.HTTP_201_CREATED)
        job_id = create_response.data['job_description']['id']
        
        # 2. Retrieve job
        detail_url = reverse('jobs:job-detail', kwargs={'pk': job_id})
        retrieve_response = self.client.get(detail_url)
        
        self.assertEqual(retrieve_response.status_code, status.HTTP_200_OK)
        self.assertEqual(retrieve_response.data['title'], 'Full Stack Developer')
        
        # 3. Update job
        update_data = {
            'title': 'Senior Full Stack Developer',
            'raw_content': create_data['raw_content']
        }
        update_response = self.client.put(detail_url, update_data, format='json')
        
        self.assertEqual(update_response.status_code, status.HTTP_200_OK)
        self.assertEqual(update_response.data['title'], 'Senior Full Stack Developer')
        
        # 4. Reprocess job
        reprocess_url = reverse('jobs:reprocess-job', kwargs={'job_id': job_id})
        
        with patch('jobs.views.extract_job_details') as mock_reprocess:
            mock_reprocess.return_value = {
                'title': 'Reprocessed Title',
                'location': 'Remote'
            }
            
            reprocess_response = self.client.put(reprocess_url)
        
        self.assertEqual(reprocess_response.status_code, status.HTTP_200_OK)
        
        # 5. Verify in list
        list_url = reverse('jobs:user-jobs')
        list_response = self.client.get(list_url)
        
        self.assertEqual(list_response.status_code, status.HTTP_200_OK)
        job_titles = [job['title'] for job in list_response.data['job_descriptions']]
        self.assertIn('Reprocessed Title', job_titles)
        
        # 6. Delete job
        delete_url = reverse('jobs:delete-job', kwargs={'job_id': job_id})
        delete_response = self.client.delete(delete_url)
        
        self.assertEqual(delete_response.status_code, status.HTTP_200_OK)
        
        # 7. Verify deletion
        final_retrieve = self.client.get(detail_url)
        self.assertEqual(final_retrieve.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_multi_user_isolation(self):
        """Test that users cannot access each other's jobs"""
        # User1 creates job
        self.authenticate_user1()
        create_url = reverse('jobs:job-create')
        
        with patch('jobs.serializers.extract_job_details'):
            response = self.client.post(create_url, {'raw_content': 'User1 job'}, format='json')
        
        job_id = response.data['job_description']['id']
        
        # User2 tries to access User1's job
        self.authenticate_user2()
        
        # Try to retrieve
        detail_url = reverse('jobs:job-detail', kwargs={'pk': job_id})
        retrieve_response = self.client.get(detail_url)
        self.assertEqual(retrieve_response.status_code, status.HTTP_404_NOT_FOUND)
        
        # Try to update
        update_response = self.client.put(detail_url, {'title': 'Hacked'}, format='json')
        self.assertEqual(update_response.status_code, status.HTTP_404_NOT_FOUND)
        
        # Try to reprocess
        reprocess_url = reverse('jobs:reprocess-job', kwargs={'job_id': job_id})
        reprocess_response = self.client.put(reprocess_url)
        self.assertEqual(reprocess_response.status_code, status.HTTP_404_NOT_FOUND)
        
        # Try to delete
        delete_url = reverse('jobs:delete-job', kwargs={'job_id': job_id})
        delete_response = self.client.delete(delete_url)
        self.assertEqual(delete_response.status_code, status.HTTP_404_NOT_FOUND)
        
        # Verify job still exists for original owner
        self.authenticate_user1()
        retrieve_response = self.client.get(detail_url)
        self.assertEqual(retrieve_response.status_code, status.HTTP_200_OK)


class JobDescriptionViewsErrorHandlingTests(BaseJobTestCase):
    """Tests for error handling scenarios"""
    
    def test_malformed_json_request(self):
        """Test handling of malformed JSON requests"""
        self.authenticate_user1()
        url = reverse('jobs:job-create')
        
        # Send malformed JSON
        response = self.client.post(
            url,
            '{"raw_content": "test" invalid json}',
            content_type='application/json'
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_oversized_file_upload(self):
        """Test handling of oversized file uploads"""
        self.authenticate_user1()
        url = reverse('jobs:job-create')
        
        # Create a large file (mock size check)
        large_content = 'x' * (10 * 1024 * 1024)  # 10MB
        large_file = self.create_test_file('large.txt', large_content)
        
        # This would normally be handled by Django's FILE_UPLOAD_MAX_MEMORY_SIZE
        # but we can test the serializer validation
        data = {'document': large_file}
        
        with patch('jobs.serializers.extract_text_from_document') as mock_extract:
            mock_extract.side_effect = ValueError('File too large')
            
            response = self.client.post(url, data, format='multipart')
        
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def test_database_error_handling(self):
        """Test handling of database errors"""
        self.authenticate_user1()
        url = reverse('jobs:job-create')
        
        data = {'raw_content': 'Test content'}
        
        with patch('jobs.models.JobDescription.objects.create') as mock_create:
            mock_create.side_effect = Exception('Database error')
            
            response = self.client.post(url, data, format='json')
        
        # The error should be handled gracefully
        self.assertIn(response.status_code, [status.HTTP_400_BAD_REQUEST, status.HTTP_500_INTERNAL_SERVER_ERROR])
    
    def test_concurrent_access_same_job(self):
        """Test concurrent access to the same job"""
        self.authenticate_user1()
        
        # Simulate concurrent updates
        detail_url = reverse('jobs:job-detail', kwargs={'pk': self.job1.id})
        
        update_data1 = {'title': 'Update 1'}
        update_data2 = {'title': 'Update 2'}
        
        # Both updates should succeed (last one wins)
        response1 = self.client.patch(detail_url, update_data1, format='json')
        response2 = self.client.patch(detail_url, update_data2, format='json')
        
        self.assertEqual(response1.status_code, status.HTTP_200_OK)
        self.assertEqual(response2.status_code, status.HTTP_200_OK)
        
        # Check final state
        self.job1.refresh_from_db()
        self.assertEqual(self.job1.title, 'Update 2')


class JobDescriptionViewsPerformanceTests(BaseJobTestCase):
    """Tests for performance-related scenarios"""
    
    def test_large_job_description_processing(self):
        """Test processing of large job descriptions"""
        self.authenticate_user1()
        
        # Create large content
        large_content = 'Job description content.' * 1000  # ~25KB
        data = {'raw_content': large_content}
        
        url = reverse('jobs:job-create')
        
        with patch('jobs.serializers.extract_job_details') as mock_extract:
            mock_extract.return_value = {'title': 'Large Job'}
            
            response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        job = JobDescription.objects.get(id=response.data['job_description']['id'])
        self.assertEqual(len(job.raw_content), len(large_content))
    
    def test_list_view_with_many_jobs(self):
        """Test list view performance with many jobs"""
        self.authenticate_user1()
        
        # Create many jobs
        jobs = []
        for i in range(50):
            job = JobDescription.objects.create(
                user=self.user1,
                raw_content=f'Job content {i}',
                title=f'Job {i}',
                company=f'Company {i}'
            )
            jobs.append(job)
        
        url = reverse('jobs:user-jobs')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 52)  # 50 + 2 from setUp
        self.assertEqual(len(response.data['job_descriptions']), 52)


class JobDescriptionViewsEdgeCaseTests(BaseJobTestCase):
    """Tests for edge cases and boundary conditions"""
    
    def test_job_with_unicode_content(self):
        """Test handling of Unicode content"""
        self.authenticate_user1()
        
        unicode_content = """
        Software Engineer Position 🚀
        Company: TechCorp™ 
        Location: São Paulo, Brazil 🇧🇷
        Requirements: 
        - Experience with résumé processing
        - Knowledge of différent languages
        - Ability to work with ñoñ-ASCII characters
        """
        
        data = {'raw_content': unicode_content}
        url = reverse('jobs:job-create')
        
        with patch('jobs.serializers.extract_job_details') as mock_extract:
            mock_extract.return_value = {
                'title': 'Software Engineer Position 🚀',
                'company': 'TechCorp™'
            }
            
            response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        job = JobDescription.objects.get(id=response.data['job_description']['id'])
        self.assertIn('🚀', job.raw_content)
        self.assertIn('São Paulo', job.raw_content)
    
    def test_job_with_very_long_fields(self):
        """Test handling of very long field values"""
        self.authenticate_user1()
        
        # Create job with long title (exceeding CharField max_length)
        long_title = 'A' * 300  # Exceeds 200 char limit
        long_company = 'B' * 300
        
        data = {'raw_content': 'Content with long extracted fields'}
        url = reverse('jobs:job-create')
        
        with patch('jobs.serializers.extract_job_details') as mock_extract:
            mock_extract.return_value = {
                'title': long_title,
                'company': long_company
            }
            
            response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        job = JobDescription.objects.get(id=response.data['job_description']['id'])
        # Fields should be truncated to max_length
        self.assertEqual(len(job.title), 200)
        self.assertEqual(len(job.company), 200)
    
    def test_job_type_choices_validation(self):
        """Test job_type field choices validation"""
        self.authenticate_user1()
        
        data = {'raw_content': 'Test content'}
        url = reverse('jobs:job-create')
        
        # Test valid job_type
        with patch('jobs.serializers.extract_job_details') as mock_extract:
            mock_extract.return_value = {'job_type': 'remote'}
            response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        job = JobDescription.objects.get(id=response.data['job_description']['id'])
        self.assertEqual(job.job_type, 'remote')
        
        # Test invalid job_type gets converted to default
        with patch('jobs.serializers.extract_job_details') as mock_extract:
            mock_extract.return_value = {'job_type': 'invalid_type'}
            response = self.client.post(url, data, format='json')
        
        # Should still create job with default value
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
    
    def test_empty_extraction_results(self):
        """Test handling of empty extraction results"""
        self.authenticate_user1()
        
        data = {'raw_content': 'Minimal content'}
        url = reverse('jobs:job-create')
        
        with patch('jobs.serializers.extract_job_details') as mock_extract:
            mock_extract.return_value = {}  # Empty extraction
            response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        job = JobDescription.objects.get(id=response.data['job_description']['id'])
        self.assertTrue(job.is_processed)
        self.assertEqual(job.title, '')  # Should remain empty
        self.assertEqual(job.company, '')
    
    def test_none_values_in_extraction(self):
        """Test handling of None values in extraction results"""
        self.authenticate_user1()
        
        data = {'raw_content': 'Content with None extractions'}
        url = reverse('jobs:job-create')
        
        with patch('jobs.serializers.extract_job_details') as mock_extract:
            mock_extract.return_value = {
                'title': None,
                'company': 'Valid Company',
                'location': None,
                'salary_range': ''
            }
            response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        job = JobDescription.objects.get(id=response.data['job_description']['id'])
        self.assertEqual(job.title, '')  # None should not be set
        self.assertEqual(job.company, 'Valid Company')
        self.assertIsNone(job.location)  # Should remain None for nullable field


class JobDescriptionViewsSecurityTests(BaseJobTestCase):
    """Tests for security-related scenarios"""
    
    def test_sql_injection_attempt(self):
        """Test SQL injection attempts in content"""
        self.authenticate_user1()
        
        malicious_content = "'; DROP TABLE jobs_jobdescription; --"
        data = {'raw_content': malicious_content}
        url = reverse('jobs:job-create')
        
        with patch('jobs.serializers.extract_job_details') as mock_extract:
            mock_extract.return_value = {'title': 'Safe Title'}
            response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Verify table still exists and content is safely stored
        self.assertTrue(JobDescription.objects.filter(
            raw_content=malicious_content
        ).exists())
    
    def test_xss_attempt_in_content(self):
        """Test XSS attempts in job content"""
        self.authenticate_user1()
        
        xss_content = '<script>alert("XSS")</script>'
        data = {'raw_content': xss_content}
        url = reverse('jobs:job-create')
        
        with patch('jobs.serializers.extract_job_details') as mock_extract:
            mock_extract.return_value = {'title': '<script>alert("XSS")</script>'}
            response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Content should be stored as-is (escaping happens in templates)
        job = JobDescription.objects.get(id=response.data['job_description']['id'])
        self.assertEqual(job.raw_content, xss_content)
    
    def test_path_traversal_in_filename(self):
        """Test path traversal attempts in filenames"""
        self.authenticate_user1()
        
        malicious_filename = '../../../etc/passwd.docx'
        test_file = SimpleUploadedFile(
            malicious_filename,
            b'malicious content',
            content_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        )
        
        data = {'document': test_file}
        url = reverse('jobs:job-create')
        
        with patch('jobs.serializers.extract_text_from_document') as mock_extract:
            mock_extract.return_value = 'Extracted content'
            
            with patch('jobs.serializers.extract_job_details'):
                response = self.client.post(url, data, format='multipart')
        
        # Expect success (sanitized)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        job = JobDescription.objects.get(id=response.data['job_description']['id'])
        self.assertNotIn('..', job.document.name)
        self.assertTrue(job.document.name.endswith('passwd.docx'))





# ✅ Test utilities
class JobDescriptionTestUtilities:
    """Utility class for test helpers"""

    @staticmethod
    def create_mock_extraction_results():
        """Create mock extraction results for testing"""
        return {
            'title': 'Mock Job Title',
            'company': 'Mock Company',
            'location': 'Mock Location',
            'job_type': 'full_time',
            'salary_range': '$50,000 - $70,000',
            'requirements': 'Mock requirements',
            'skills_required': 'Python, Django, REST API',
            'experience_level': 'Mid-level'
        }

    @staticmethod
    def assert_job_response_structure(test_case, response_data):
        """Assert the structure of job response data"""
        required_fields = [
            'id', 'user', 'raw_content', 'title', 'company',
            'created_at', 'updated_at', 'is_processed'
        ]
        for field in required_fields:
            test_case.assertIn(field, response_data)

class JobDescriptionViewsTestConfig:
    """Configuration for running job description view tests"""
    TEST_MEDIA_ROOT = '/tmp/django_test_media'

    MOCK_EXTRACTION_SUCCESS = {
        'title': 'Test Job',
        'company': 'Test Company'
    }

    # Simulate an error that can be raised in tests
    MOCK_EXTRACTION_ERROR = Exception('Extraction failed')


# Example test case that might have been intended:
class JobDescriptionViewTest(BaseJobTestCase):

    def setUp(self):
        super().setUp()
        self.url = reverse('jobs:job-create')

    def tearDown(self):
        super().tearDown()
        # Clean up uploaded files and database records
        for job in JobDescription.objects.all():
            if job.document:
                job.document.delete()
        JobDescription.objects.all().delete()


    def test_create_job_description(self):
        self.authenticate_user1()  # Add authentication
        response = self.client.post(
            self.url,  # Use reverse('jobs:job-create')
            {'raw_content': 'New job description content'},
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('message', response.data)
        self.assertIn('job_description', response.data)
        self.assertIn('extraction_status', response.data)
        
        job = JobDescription.objects.get(id=response.data['job_description']['id'])
        self.assertEqual(job.user, self.user1)
        self.assertEqual(job.raw_content, 'New job description content')
        self.assertTrue(job.is_processed)
    
    def test_create_job_with_document_authenticated(self):
        """Test creating job description with document upload"""
        self.authenticate_user1()
        
        test_file = self.create_test_file('test_job.txt', 'Job description from file')
        data = {
            'document': test_file,
            'is_active': True
        }
        
        with patch('jobs.serializers.extract_text_from_document') as mock_extract_text, \
             patch('jobs.serializers.extract_job_details') as mock_extract_details:
            
            mock_extract_text.return_value = 'Extracted text from document'
            mock_extract_details.return_value = {
                'title': 'File Job',
                'company': 'File Company'
            }
            
            response = self.client.post(self.url, data, format='multipart')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Verify document was saved
        job = JobDescription.objects.get(id=response.data['job_description']['id'])
        self.assertTrue(job.document)
        self.assertEqual(job.raw_content, 'Extracted text from document')
    
    def test_create_job_with_both_content_and_document(self):
        """Test creating job with both text content and document"""
        self.authenticate_user1()
        
        test_file = self.create_test_file('test_job.txt', 'Document content')
        data = {
            'raw_content': 'Text content',
            'document': test_file,
            'is_active': True
        }
        
        with patch('jobs.serializers.extract_text_from_document') as mock_extract_text, \
             patch('jobs.serializers.extract_job_details') as mock_extract_details:
            
            mock_extract_text.return_value = 'Document content'
            mock_extract_details.return_value = {'title': 'Combined Job'}
            
            response = self.client.post(self.url, data, format='multipart')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        job = JobDescription.objects.get(id=response.data['job_description']['id'])
        expected_content = 'Text content\n\n--- From Document ---\nDocument content'
        self.assertEqual(job.raw_content, expected_content)
    
    def test_create_job_unauthenticated(self):
        """Test creating job description without authentication"""
        self.unauthenticate()
        data = {'raw_content': 'Test content'}
        
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_create_job_no_content_or_document(self):
        """Test validation error when neither content nor document provided"""
        self.authenticate_user1()
        data = {'is_active': True}
        
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('Either upload a document or provide job description text', 
                      str(response.data))
    
    def test_create_job_invalid_file_type(self):
        """Test validation error for invalid file types"""
        self.authenticate_user1()
        
        invalid_file = self.create_test_file('test.exe', 'Invalid content')
        data = {'document': invalid_file}
        
        response = self.client.post(self.url, data, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('Unsupported file type', str(response.data))
    
    def test_create_job_document_processing_error(self):
        """Test handling of document processing errors"""
        self.authenticate_user1()
        
        test_file = self.create_test_file('test.pdf', 'PDF content')
        data = {'document': test_file}
        
        with patch('jobs.serializers.extract_text_from_document') as mock_extract:
            mock_extract.side_effect = ValueError('Document processing failed')
            
            response = self.client.post(self.url, data, format='multipart')
        
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertIn('Document processing error', str(response.data))
    
    def test_create_job_extraction_error(self):
        """Test handling of job details extraction errors"""
        self.authenticate_user1()
        data = {'raw_content': 'Test content'}
        
        with patch('jobs.serializers.extract_job_details') as mock_extract:
            mock_extract.side_effect = Exception('Extraction failed')
            
            response = self.client.post(self.url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Job should be created but not processed
        job = JobDescription.objects.get(id=response.data['job_description']['id'])
        self.assertFalse(job.is_processed)
        self.assertIn('Error extracting details', job.processing_notes)
    
    def test_create_job_valid_file_types(self):
        """Test creating jobs with all valid file types"""
        self.authenticate_user1()
        valid_extensions = ['pdf', 'docx', 'doc', 'txt']
        
        for ext in valid_extensions:
            with self.subTest(extension=ext):
                test_file = self.create_test_file(f'test.{ext}', f'Content for {ext}')
                data = {'document': test_file}
                try:
                    with patch('jobs.serializers.extract_text_from_document') as mock_extract_text, \
                        patch('jobs.serializers.extract_job_details') as mock_extract_details:
                        
                        mock_extract_text.return_value = f'Extracted content for {ext}'  # Return string
                        mock_extract_details.return_value = {
                            'title': f'Test Job {ext}',
                            'company': 'Test Company',
                            'location': 'Test Location',
                            'job_type': 'full_time',
                            'salary_range': '$50,000-$70,000',
                            'requirements': 'Test requirements',
                            'skills_required': 'Python, Django',
                            'experience_level': 'Mid-level'
                        }
                        
                        response = self.client.post(self.url, data, format='multipart')
                    
                    self.assertEqual(response.status_code, status.HTTP_201_CREATED)
                    job = JobDescription.objects.get(id=response.data['job_description']['id'])
                    self.assertEqual(job.raw_content, f'Extracted content for {ext}')
                    self.assertEqual(job.title, f'Test Job {ext}')
                    self.assertEqual(job.company, 'Test Company')
                finally:
                    test_file.close()


class JobDescriptionDetailViewTests(BaseJobTestCase):
    """Tests for JobDescriptionDetailView"""
    
    def setUp(self):
        super().setUp()
        self.url = lambda job_id: reverse('jobs:job-detail', kwargs={'pk': job_id})
    
    def test_retrieve_job_authenticated_owner(self):
        """Test retrieving job description by owner"""
        self.authenticate_user1()
        
        response = self.client.get(self.url(self.job1.id))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], self.job1.id)
        self.assertEqual(response.data['title'], self.job1.title)
    
    def test_retrieve_job_authenticated_non_owner(self):
        """Test retrieving job description by non-owner (should fail)"""
        self.authenticate_user2()
        
        response = self.client.get(self.url(self.job1.id))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_retrieve_job_unauthenticated(self):
        """Test retrieving job description without authentication"""
        self.unauthenticate()
        
        response = self.client.get(self.url(self.job1.id))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_retrieve_nonexistent_job(self):
        """Test retrieving non-existent job description"""
        self.authenticate_user1()
        
        response = self.client.get(self.url(99999))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_update_job_authenticated_owner(self):
        """Test updating job description by owner"""
        self.authenticate_user1()
        
        update_data = {
            'title': 'Updated Job Title',
            'company': 'Updated Company',
            'raw_content': self.job1.raw_content  # Required field
        }
        
        response = self.client.put(self.url(self.job1.id), update_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify update
        self.job1.refresh_from_db()
        self.assertEqual(self.job1.title, 'Updated Job Title')
        self.assertEqual(self.job1.company, 'Updated Company')
    
    def test_partial_update_job(self):
        """Test partial update of job description"""
        self.authenticate_user1()
        
        update_data = {'title': 'Partially Updated Title'}
        
        response = self.client.patch(self.url(self.job1.id), update_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        self.job1.refresh_from_db()
        self.assertEqual(self.job1.title, 'Partially Updated Title')
        # Other fields should remain unchanged
        self.assertEqual(self.job1.company, 'TechCorp Inc.')
    
    def test_update_job_authenticated_non_owner(self):
        """Test updating job description by non-owner (should fail)"""
        self.authenticate_user2()
        
        update_data = {'title': 'Unauthorized Update'}
        
        response = self.client.patch(self.url(self.job1.id), update_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_delete_job_authenticated_owner(self):
        """Test deleting job description by owner"""
        self.authenticate_user1()
        
        # Create a job with document for deletion test
        test_file = self.create_test_file('test_delete.txt', 'Content to delete')
        job_with_doc = JobDescription.objects.create(
            user=self.user1,
            raw_content='Content with document',
            document=test_file
        )
        
        response = self.client.delete(self.url(job_with_doc.id))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        
        # Verify deletion
        self.assertFalse(JobDescription.objects.filter(id=job_with_doc.id).exists())
    
    def test_delete_job_authenticated_non_owner(self):
        """Test deleting job description by non-owner (should fail)"""
        self.authenticate_user2()
        
        response = self.client.delete(self.url(self.job1.id))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        
        # Verify job still exists
        self.assertTrue(JobDescription.objects.filter(id=self.job1.id).exists())


class PasteJobDescriptionViewTests(BaseJobTestCase):
    """Tests for PasteJobDescriptionView"""
    
    def setUp(self):
        super().setUp()
        self.url = reverse('jobs:paste-job')  # Adjust URL name as needed
    
    def test_paste_job_content_authenticated(self):
        """Test pasting job description content"""
        self.authenticate_user1()
        
        data = {'content': 'Pasted job description content'}
        
        with patch('jobs.serializers.extract_job_details') as mock_extract:
            mock_extract.return_value = {
                'title': 'Pasted Job',
                'company': 'Pasted Company'
            }
            
            response = self.client.post(self.url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('message', response.data)
        self.assertIn('pasted and processed successfully', response.data['message'])
        
        # Verify job was created
        job = JobDescription.objects.get(id=response.data['job_description']['id'])
        self.assertEqual(job.raw_content, 'Pasted job description content')
        self.assertEqual(job.user, self.user1)
    
    def test_paste_job_empty_content(self):
        """Test pasting empty content"""
        self.authenticate_user1()
        
        data = {'content': ''}
        response = self.client.post(self.url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('Job description content is required', response.data['message'])
    
    def test_paste_job_whitespace_content(self):
        """Test pasting whitespace-only content"""
        self.authenticate_user1()
        
        data = {'content': '   \n\t   '}
        response = self.client.post(self.url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('Job description content is required', response.data['message'])
    
    def test_paste_job_no_content_field(self):
        """Test pasting without content field"""
        self.authenticate_user1()
        
        data = {}
        response = self.client.post(self.url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('Job description content is required', response.data['message'])
    
    def test_paste_job_unauthenticated(self):
        """Test pasting job description without authentication"""
        self.unauthenticate()
        
        data = {'content': 'Unauthorized paste'}
        response = self.client.post(self.url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_paste_job_extraction_error(self):
        """Test handling extraction errors during paste"""
        self.authenticate_user1()
        
        data = {'content': 'Content with extraction error'}
        
        with patch('jobs.serializers.extract_job_details') as mock_extract:
            mock_extract.side_effect = Exception('Extraction failed')
            
            response = self.client.post(self.url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Job should be created but not processed
        job = JobDescription.objects.get(id=response.data['job_description']['id'])
        self.assertFalse(job.is_processed)
        self.assertIn('Error extracting details', job.processing_notes)


class UserJobListViewTests(BaseJobTestCase):
    """Tests for UserJobListView"""
    
    def setUp(self):
        super().setUp()
        self.url = reverse('jobs:user-jobs')  # Adjust URL name as needed
    
    def test_list_user_jobs_authenticated(self):
        """Test listing jobs for authenticated user"""
        self.authenticate_user1()
        
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Check response structure
        self.assertIn('count', response.data)
        self.assertIn('processed_count', response.data)
        self.assertIn('job_descriptions', response.data)
        
        # Verify counts
        self.assertEqual(response.data['count'], 2)  # user1 has 2 jobs
        self.assertEqual(response.data['processed_count'], 1)  # only job1 is processed
        
        # Verify only user's jobs are returned
        job_ids = [job['id'] for job in response.data['job_descriptions']]
        self.assertIn(self.job1.id, job_ids)
        self.assertIn(self.job2.id, job_ids)
        self.assertNotIn(self.job_user2.id, job_ids)
    
    def test_list_jobs_different_user(self):
        """Test that each user sees only their own jobs"""
        self.authenticate_user2()
        
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        self.assertEqual(response.data['count'], 1)  # user2 has 1 job
        job_ids = [job['id'] for job in response.data['job_descriptions']]
        self.assertEqual(job_ids, [self.job_user2.id])
    
    def test_list_jobs_unauthenticated(self):
        """Test listing jobs without authentication"""
        self.unauthenticate()
        
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_list_jobs_empty_result(self):
        """Test listing jobs when user has no jobs"""
        # Create new user with no jobs
        new_user = User.objects.create_user(
            username='newuser',
            email='new@example.com',
            password='newpass123'
        )
        
        new_token = AccessToken.for_user(user=new_user)
        #self.client.credentials(HTTP_AUTHORIZATION=f'Token {new_token.key}')
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {str(new_token)}')
        
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 0)
        self.assertEqual(response.data['processed_count'], 0)
        self.assertEqual(response.data['job_descriptions'], [])
    
    def test_list_jobs_ordering(self):
        """Test that jobs are ordered by creation date (newest first)"""
        self.authenticate_user1()
        
        # Create additional job to test ordering
        newer_job = JobDescription.objects.create(
            user=self.user1,
            raw_content='Newer job content',
            title='Newer Job'
        )
        
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        job_ids = [job['id'] for job in response.data['job_descriptions']]
        # Should be ordered by creation date (newest first)
        self.assertEqual(job_ids[0], newer_job.id)


class JobReprocessViewTests(BaseJobTestCase):
    """Tests for JobReprocessView"""
    
    def setUp(self):
        super().setUp()
        self.url = lambda job_id: reverse('jobs:reprocess-job', kwargs={'job_id': job_id})
    
    def test_reprocess_job_authenticated_owner(self):
        """Test reprocessing job by owner"""
        self.authenticate_user1()
        
        with patch('jobs.views.extract_job_details') as mock_extract:
            mock_extract.return_value = {
                'title': 'Reprocessed Job',
                'company': 'Reprocessed Company',
                'location': 'New Location'
            }
            
            response = self.client.put(self.url(self.job2.id))
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('reprocessed successfully', response.data['message'])
        
        # Verify job was updated
        self.job2.refresh_from_db()
        self.assertTrue(self.job2.is_processed)
        self.assertEqual(self.job2.title, 'Reprocessed Job')
        self.assertEqual(self.job2.company, 'Reprocessed Company')
        self.assertEqual(self.job2.location, 'New Location')
        self.assertIn('Successfully reprocessed', self.job2.processing_notes)
    
    def test_reprocess_job_authenticated_non_owner(self):
        """Test reprocessing job by non-owner (should fail)"""
        self.authenticate_user2()
        
        response = self.client.put(self.url(self.job1.id))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_reprocess_job_unauthenticated(self):
        """Test reprocessing job without authentication"""
        self.unauthenticate()
        
        response = self.client.put(self.url(self.job1.id))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_reprocess_job_no_raw_content(self):
        """Test reprocessing job with no raw content"""
        self.authenticate_user1()
        
        # Create job without raw content
        empty_job = JobDescription.objects.create(
            user=self.user1,
            raw_content='',
            title='Empty Job'
        )
        
        response = self.client.put(self.url(empty_job.id))
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('No raw content available', response.data['message'])
    
    def test_reprocess_job_extraction_error(self):
        """Test reprocessing job with extraction error"""
        self.authenticate_user1()
        
        with patch('jobs.views.extract_job_details') as mock_extract:
            mock_extract.side_effect = Exception('Reprocessing failed')
            
            response = self.client.put(self.url(self.job2.id))
        
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertIn('Error reprocessing', response.data['message'])
        
        # Verify job processing status was updated
        self.job2.refresh_from_db()
        self.assertFalse(self.job2.is_processed)
        self.assertIn('Error during reprocessing', self.job2.processing_notes)
    
    def test_reprocess_job_nonexistent(self):
        """Test reprocessing non-existent job"""
        self.authenticate_user1()
        
        response = self.client.put(self.url(99999))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_reprocess_job_partial_extraction(self):
        """Test reprocessing with partial extraction results"""
        self.authenticate_user1()
        
        with patch('jobs.views.extract_job_details') as mock_extract:
            # Return partial data with some empty values
            mock_extract.return_value = {
                'title': 'New Title',
                'company': '',  # Empty value should not be set
                'location': 'New Location',
                'skills_required': None  # None value should not be set
            }
            
            response = self.client.put(self.url(self.job2.id))
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        self.job2.refresh_from_db()
        self.assertEqual(self.job2.title, 'New Title')
        self.assertEqual(self.job2.location, 'New Location')
        # Empty/None values should not overwrite existing data
        self.assertEqual(self.job2.company, 'DataCorp')  # Original value preserved


class JobDeleteViewTests(BaseJobTestCase):
    """Tests for JobDeleteView"""
    
    def setUp(self):
        super().setUp()
        self.url = lambda job_id: reverse('jobs:delete-job', kwargs={'job_id': job_id})
    
    def test_delete_job_authenticated_owner(self):
        """Test deleting job by owner"""
        self.authenticate_user1()
        
        job_id = self.job1.id
        response = self.client.delete(self.url(job_id))
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('deleted successfully', response.data['message'])
        
        # Verify job was deleted
        self.assertFalse(JobDescription.objects.filter(id=job_id).exists())
    
    def test_delete_job_authenticated_non_owner(self):
        """Test deleting job by non-owner (should fail)"""
        self.authenticate_user2()
        
        response = self.client.delete(self.url(self.job1.id))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        
        # Verify job still exists
        self.assertTrue(JobDescription.objects.filter(id=self.job1.id).exists())
    
    def test_delete_job_unauthenticated(self):
        """Test deleting job without authentication"""
        self.unauthenticate()
        
        response = self.client.delete(self.url(self.job1.id))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        
        # Verify job still exists
        self.assertTrue(JobDescription.objects.filter(id=self.job1.id).exists())
    
    def test_delete_job_nonexistent(self):
        """Test deleting non-existent job"""
        self.authenticate_user1()
        
        response = self.client.delete(self.url(99999))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_delete_job_with_document(self):
        """Test deleting job with associated document file"""
        self.authenticate_user1()
        
        # Create job with document
        with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
            tmp_file.write(b'Test document content')
            tmp_file_path = tmp_file.name
        
        with open(tmp_file_path, 'rb') as f:
            test_file = SimpleUploadedFile('test_doc.txt', f.read())
            job_with_doc = JobDescription.objects.create(
                user=self.user1,
                raw_content='Job with document',
                document=test_file
            )
        
        # Mock the file path checking
        with patch('os.path.isfile', return_value=True), \
             patch('os.remove') as mock_remove:  # noqa: F841
            
            response = self.client.delete(self.url(job_with_doc.id))
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)