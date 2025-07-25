from unittest.mock import patch, Mock
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils import timezone
from rest_framework.test import APIRequestFactory
from rest_framework.request import Request

from jobs.models import JobDescription
from jobs.serializers import (
    JobDescriptionSerializer,
    JobDescriptionUploadSerializer,
    JobDescriptionListSerializer
)

User = get_user_model()


class BaseSerializerTestCase(TestCase):
    """Base test case with common setup for all serializer tests"""
    
    def setUp(self):
        self.factory = APIRequestFactory()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.other_user = User.objects.create_user(
            username='otheruser',
            email='other@example.com',
            password='testpass123'
        )
        
        # Create test job descriptions
        self.job_description = JobDescription.objects.create(
            user=self.user,
            raw_content="Software Engineer position at TechCorp",
            title="Software Engineer",
            company="TechCorp",
            location="New York, NY",
            job_type="full_time",
            salary_range="$80,000 - $120,000",
            requirements="Bachelor's degree in Computer Science",
            skills_required="Python, Django, JavaScript",
            experience_level="Mid-level",
            is_processed=True,
            processing_notes="Successfully processed"
        )
        
        self.processed_job = JobDescription.objects.create(
            user=self.user,
            raw_content="Data Scientist role",
            title="Data Scientist",
            company="DataCorp",
            is_processed=True
        )
        
        self.unprocessed_job = JobDescription.objects.create(
            user=self.user,
            raw_content="Marketing Manager position",
            is_processed=False,
            processing_notes="Failed to extract details"
        )

    def create_test_file(self, filename, content, content_type='text/plain'):
        """Helper method to create test files"""
        return SimpleUploadedFile(
            filename, 
            content.encode('utf-8'), 
            content_type=content_type
        )
    
    def create_request_with_user(self, user=None):
        """Helper method to create request with authenticated user"""
        request = self.factory.get('/')
        # Ensure a valid User instance is used; defaultxyz
        request.user = user or self.user
        if not request.user.is_authenticated:
            raise ValueError("Request user must be an authenticated User instance")
        return Request(request)


class JobDescriptionSerializerTest(BaseSerializerTestCase):
    """Tests for JobDescriptionSerializer"""
    
    def test_serialization_complete_job(self):
        """Test serialization of complete job description"""
        serializer = JobDescriptionSerializer(self.job_description)
        data = serializer.data
        
        expected_fields = [
            'id', 'user', 'raw_content', 'document', 'document_name',
            'title', 'company', 'location', 'job_type', 'salary_range',
            'requirements', 'skills_required', 'experience_level',
            'is_processed', 'processing_notes', 'created_at', 
            'updated_at', 'is_active'
        ]
        
        for field in expected_fields:
            self.assertIn(field, data)
        
        self.assertEqual(data['id'], self.job_description.id)
        self.assertEqual(data['user'], str(self.user))
        self.assertEqual(data['raw_content'], "Software Engineer position at TechCorp")
        self.assertEqual(data['title'], "Software Engineer")
        self.assertEqual(data['company'], "TechCorp")
        self.assertEqual(data['location'], "New York, NY")
        self.assertEqual(data['job_type'], "full_time")
        self.assertEqual(data['salary_range'], "$80,000 - $120,000")
        self.assertEqual(data['requirements'], "Bachelor's degree in Computer Science")
        self.assertEqual(data['skills_required'], "Python, Django, JavaScript")
        self.assertEqual(data['experience_level'], "Mid-level")
        self.assertTrue(data['is_processed'])
        self.assertEqual(data['processing_notes'], "Successfully processed")
        self.assertTrue(data['is_active'])
        self.assertIsNone(data['document_name'])
    
    def test_serialization_with_document(self):
        """Test serialization when document is present"""
        # Create job with document
        test_file = self.create_test_file('test_job.txt', 'Job content')
        job_with_doc = JobDescription.objects.create(
            user=self.user,
            raw_content="Test content",
            document=test_file
        )
        
        serializer = JobDescriptionSerializer(job_with_doc)
        data = serializer.data
        
        self.assertIsNotNone(data['document'])
        self.assertEqual(data['document_name'], 'test_job.txt')
    
    def test_serialization_minimal_job(self):
        """Test serialization of minimal job description"""
        minimal_job = JobDescription.objects.create(
            user=self.user,
            raw_content="Minimal job description"
        )
        
        serializer = JobDescriptionSerializer(minimal_job)
        data = serializer.data
        
        self.assertEqual(data['title'], '')
        self.assertEqual(data['company'], '')
        self.assertIsNone(data['location'])
        self.assertEqual(data['job_type'], 'unknown')
        self.assertIsNone(data['salary_range'])
        self.assertFalse(data['is_processed'])
    
    def test_read_only_fields(self):
        """Test that read-only fields cannot be updated"""
        serializer = JobDescriptionSerializer(
            self.job_description,
            data={
                'id': 999,
                'user': 'different_user',
                'created_at': timezone.now(),
                'updated_at': timezone.now(),
                'is_processed': False,
                'processing_notes': 'Updated notes',
                'document_name': 'new_name.txt',
                'title': 'Updated Title'
            },
            partial=True
        )
        
        self.assertTrue(serializer.is_valid())
        updated_job = serializer.save()
        
        # Read-only fields should not change
        self.assertNotEqual(updated_job.id, 999)
        self.assertEqual(updated_job.user, self.user)
        self.assertTrue(updated_job.is_processed)  # Should remain True
        self.assertEqual(updated_job.processing_notes, "Successfully processed")
        
        # Non-read-only fields should update
        self.assertEqual(updated_job.title, 'Updated Title')
    
    def test_get_document_name_no_document(self):
        """Test get_document_name when no document exists"""
        serializer = JobDescriptionSerializer(self.job_description)
        self.assertIsNone(serializer.get_document_name(self.job_description))
    
    def test_get_document_name_with_path(self):
        """Test get_document_name extracts filename from path"""
        mock_job = Mock()
        mock_job.document = Mock()
        mock_job.document.name = 'path/to/document/resume.pdf'
        
        serializer = JobDescriptionSerializer()
        result = serializer.get_document_name(mock_job)
        self.assertEqual(result, 'resume.pdf')
    
    def test_multiple_job_serialization(self):
        """Test serializing multiple job descriptions"""
        jobs = [self.job_description, self.processed_job, self.unprocessed_job]
        serializer = JobDescriptionSerializer(jobs, many=True)
        data = serializer.data
        
        self.assertEqual(len(data), 3)
        self.assertEqual(data[0]['id'], self.job_description.id)
        self.assertEqual(data[1]['id'], self.processed_job.id)
        self.assertEqual(data[2]['id'], self.unprocessed_job.id)


class JobDescriptionUploadSerializerTest(BaseSerializerTestCase):
    """Tests for JobDescriptionUploadSerializer"""
    
    def setUp(self):
        super().setUp()
        self.valid_pdf_file = self.create_test_file('test.pdf', 'PDF content')
        self.valid_docx_file = self.create_test_file('test.docx', 'DOCX content')
        self.valid_txt_file = self.create_test_file('test.txt', 'Text content')
        self.invalid_file = self.create_test_file('test.exe', 'Invalid content')
    
    def test_valid_data_with_document_only(self):
        """Test validation with valid document only"""
        data = {'document': self.valid_pdf_file}
        serializer = JobDescriptionUploadSerializer(data=data)
        
        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.validated_data['document'], self.valid_pdf_file)
    
    def test_valid_data_with_raw_content_only(self):
        """Test validation with raw content only"""
        data = {'raw_content': 'Job description content'}
        serializer = JobDescriptionUploadSerializer(data=data)
        
        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.validated_data['raw_content'], 'Job description content')
    
    def test_valid_data_with_both_document_and_content(self):
        """Test validation with both document and raw content"""
        data = {
            'document': self.valid_pdf_file,
            'raw_content': 'Additional content'
        }
        serializer = JobDescriptionUploadSerializer(data=data)
        
        self.assertTrue(serializer.is_valid())
    
    def test_validation_error_no_content(self):
        """Test validation error when neither document nor content provided"""
        data = {}
        serializer = JobDescriptionUploadSerializer(data=data)
        
        self.assertFalse(serializer.is_valid())
        self.assertIn('non_field_errors', serializer.errors)
        self.assertEqual(
            serializer.errors['non_field_errors'][0],
            "Either upload a document or provide job description text."
        )
    
    def test_validation_error_empty_content(self):
        """Test validation error with empty raw content"""
        data = {'raw_content': '   '}  # Only whitespace
        serializer = JobDescriptionUploadSerializer(data=data)
        
        self.assertFalse(serializer.is_valid())
        self.assertIn('non_field_errors', serializer.errors)
    
    def test_validation_supported_file_extensions(self):
        """Test validation of supported file extensions"""
        supported_files = [
            self.create_test_file('test.pdf', 'content'),
            self.create_test_file('test.docx', 'content'),
            self.create_test_file('test.doc', 'content'),
            self.create_test_file('test.txt', 'content'),
            self.create_test_file('TEST.PDF', 'content'),  # Case insensitive
        ]
        
        for test_file in supported_files:
            data = {'document': test_file}
            serializer = JobDescriptionUploadSerializer(data=data)
            self.assertTrue(serializer.is_valid(), f"Failed for {test_file.name}")
    
    def test_validation_unsupported_file_extension(self):
        """Test validation error for unsupported file extensions"""
        unsupported_files = [
            self.create_test_file('test.exe', 'content'),
            self.create_test_file('test.jpg', 'content'),
            self.create_test_file('test.zip', 'content'),
            self.create_test_file('test', 'content'),  # No extension
        ]
        
        for test_file in unsupported_files:
            data = {'document': test_file}
            serializer = JobDescriptionUploadSerializer(data=data)
            self.assertFalse(serializer.is_valid(), f"Should fail for {test_file.name}")
            self.assertIn('non_field_errors', serializer.errors)
            self.assertIn('Unsupported file type', str(serializer.errors))
    
    @patch('jobs.serializers.extract_text_from_document')
    @patch('jobs.serializers.extract_job_details')
    def test_create_with_document_success(self, mock_extract_details, mock_extract_text):
        """Test successful creation with document"""
        mock_extract_text.return_value = "Extracted text from document"
        mock_extract_details.return_value = {
            'title': 'Software Engineer',
            'company': 'TechCorp',
            'location': 'Remote',
        }
        
        request = self.create_request_with_user()
        serializer = JobDescriptionUploadSerializer(
            data={'document': self.valid_pdf_file},
            context={'request': request}
        )
        
        self.assertTrue(serializer.is_valid())
        job = serializer.save()
        
        self.assertEqual(job.user, self.user)
        self.assertEqual(job.raw_content, "Extracted text from document")
        self.assertEqual(job.title, 'Software Engineer')
        self.assertEqual(job.company, 'TechCorp')
        self.assertEqual(job.location, 'Remote')
        self.assertTrue(job.is_processed)
        self.assertEqual(job.processing_notes, "Successfully extracted job details")
        
        mock_extract_text.assert_called_once_with(self.valid_pdf_file)
        mock_extract_details.assert_called_once_with("Extracted text from document")
    
    @patch('jobs.serializers.extract_text_from_document')
    @patch('jobs.serializers.extract_job_details')
    def test_create_with_raw_content_success(self, mock_extract_details, mock_extract_text):
        """Test successful creation with raw content only"""
        mock_extract_details.return_value = {
            'title': 'Data Scientist',
            'company': 'DataCorp',
        }
        
        request = self.create_request_with_user()
        serializer = JobDescriptionUploadSerializer(
            data={'raw_content': 'Job description text'},
            context={'request': request}
        )
        
        self.assertTrue(serializer.is_valid())
        job = serializer.save()
        
        self.assertEqual(job.raw_content, 'Job description text')
        self.assertEqual(job.title, 'Data Scientist')
        self.assertEqual(job.company, 'DataCorp')
        self.assertTrue(job.is_processed)
        
        mock_extract_text.assert_not_called()
        mock_extract_details.assert_called_once_with('Job description text')
    
    @patch('jobs.serializers.extract_text_from_document')
    @patch('jobs.serializers.extract_job_details')
    def test_create_with_both_document_and_content(self, mock_extract_details, mock_extract_text):
        """Test creation with both document and raw content"""
        mock_extract_text.return_value = "Document content"
        mock_extract_details.return_value = {'title': 'Manager'}
        
        request = self.create_request_with_user()
        serializer = JobDescriptionUploadSerializer(
            data={
                'document': self.valid_pdf_file,
                'raw_content': 'User provided content'
            },
            context={'request': request}
        )
        
        self.assertTrue(serializer.is_valid())
        job = serializer.save()
        
        expected_content = "User provided content\n\n--- From Document ---\nDocument content"
        self.assertEqual(job.raw_content, expected_content)
        mock_extract_details.assert_called_once_with(expected_content)
    
    @patch('jobs.serializers.extract_text_from_document')
    def test_create_document_extraction_error(self, mock_extract_text):
        """Test handling of document extraction errors"""
        mock_extract_text.side_effect = ValueError("Could not extract text")
        
        request = self.create_request_with_user()
        serializer = JobDescriptionUploadSerializer(
            data={'document': self.valid_pdf_file},
            context={'request': request}
        )
        
        self.assertTrue(serializer.is_valid())
        
        with self.assertRaises(Exception) as context:
            serializer.save()
        
        self.assertIn("Document processing error", str(context.exception))
    
    @patch('jobs.serializers.extract_text_from_document')
    @patch('jobs.serializers.extract_job_details')
    def test_create_detail_extraction_error(self, mock_extract_details, mock_extract_text):
        """Test handling of job detail extraction errors"""
        mock_extract_text.return_value = "Document content"
        mock_extract_details.side_effect = Exception("Extraction failed")
        
        request = self.create_request_with_user()
        serializer = JobDescriptionUploadSerializer(
            data={'document': self.valid_pdf_file},
            context={'request': request}
        )
        
        self.assertTrue(serializer.is_valid())
        job = serializer.save()
        
        self.assertFalse(job.is_processed)
        self.assertIn("Error extracting details", job.processing_notes)
    
    @patch('jobs.serializers.extract_job_details')
    def test_create_with_empty_extracted_values(self, mock_extract_details):
        """Test creation when extracted details contain empty values"""
        mock_extract_details.return_value = {
            'title': 'Software Engineer',
            'company': '',  # Empty value
            'location': None,  # None value
            'requirements': 'Python skills',
        }
        
        request = self.create_request_with_user()
        serializer = JobDescriptionUploadSerializer(
            data={'raw_content': 'Job content'},
            context={'request': request}
        )
        
        self.assertTrue(serializer.is_valid())
        job = serializer.save()
        
        self.assertEqual(job.title, 'Software Engineer')
        self.assertEqual(job.company, '')  # Empty string preserved in model
        self.assertIsNone(job.location)  # None preserved
        self.assertEqual(job.requirements, 'Python skills')
    
    def test_create_with_is_active_flag(self):
        """Test creation with is_active flag"""
        request = self.create_request_with_user()
        
        # Test with is_active=False
        serializer = JobDescriptionUploadSerializer(
            data={'raw_content': 'Job content', 'is_active': False},
            context={'request': request}
        )
        
        self.assertTrue(serializer.is_valid())
        job = serializer.save()
        self.assertFalse(job.is_active)
        
        # Test default is_active=True
        serializer2 = JobDescriptionUploadSerializer(
            data={'raw_content': 'Job content 2'},
            context={'request': request}
        )
        
        self.assertTrue(serializer2.is_valid())
        job2 = serializer2.save()
        self.assertTrue(job2.is_active)
    
    def test_serializer_fields(self):
        """Test that serializer includes correct fields"""
        serializer = JobDescriptionUploadSerializer()
        expected_fields = ['raw_content', 'document', 'is_active']
        
        for field in expected_fields:
            self.assertIn(field, serializer.fields)
    
    def test_document_field_optional(self):
        """Test that document field is optional"""
        serializer = JobDescriptionUploadSerializer()
        document_field = serializer.fields['document']
        self.assertFalse(document_field.required)
        self.assertTrue(document_field.allow_null)
    
    def test_raw_content_field_optional(self):
        """Test that raw_content field is optional"""
        serializer = JobDescriptionUploadSerializer()
        raw_content_field = serializer.fields['raw_content']
        self.assertFalse(raw_content_field.required)
        self.assertTrue(raw_content_field.allow_blank)


class JobDescriptionListSerializerTest(BaseSerializerTestCase):
    """Tests for JobDescriptionListSerializer"""
    
    def test_serialization_fields(self):
        """Test that only expected fields are included"""
        serializer = JobDescriptionListSerializer(self.job_description)
        data = serializer.data
        
        expected_fields = [
            'id', 'title', 'company', 'location', 'job_type',
            'document_name', 'is_processed', 'created_at', 'is_active'
        ]
        
        self.assertEqual(set(data.keys()), set(expected_fields))
    
    def test_serialization_values(self):
        """Test serialization values"""
        serializer = JobDescriptionListSerializer(self.job_description)
        data = serializer.data
        
        self.assertEqual(data['id'], self.job_description.id)
        self.assertEqual(data['title'], "Software Engineer")
        self.assertEqual(data['company'], "TechCorp")
        self.assertEqual(data['location'], "New York, NY")
        self.assertEqual(data['job_type'], "full_time")
        self.assertIsNone(data['document_name'])
        self.assertTrue(data['is_processed'])
        self.assertTrue(data['is_active'])
    
    def test_serialization_with_document(self):
        """Test serialization when document is present"""
        test_file = self.create_test_file('job_listing.pdf', 'Content')
        job_with_doc = JobDescription.objects.create(
            user=self.user,
            raw_content="Test content",
            document=test_file,
            title="Test Job"
        )
        
        serializer = JobDescriptionListSerializer(job_with_doc)
        data = serializer.data
        
        self.assertEqual(data['document_name'], 'job_listing.pdf')
    
    def test_get_document_name_method(self):
        """Test get_document_name method"""
        serializer = JobDescriptionListSerializer()
        
        # Test with no document
        mock_job_no_doc = Mock()
        mock_job_no_doc.document = None
        self.assertIsNone(serializer.get_document_name(mock_job_no_doc))
        
        # Test with document having path
        mock_job_with_doc = Mock()
        mock_job_with_doc.document = Mock()
        mock_job_with_doc.document.name = 'uploads/user/documents/resume.docx'
        self.assertEqual(serializer.get_document_name(mock_job_with_doc), 'resume.docx')
    
    def test_multiple_jobs_serialization(self):
        """Test serializing multiple jobs"""
        jobs = JobDescription.objects.filter(user=self.user)
        serializer = JobDescriptionListSerializer(jobs, many=True)
        data = serializer.data
        
        self.assertEqual(len(data), 3)  # We have 3 jobs in setUp
        
        # Check that all jobs are included
        job_ids = [item['id'] for item in data]
        expected_ids = [self.job_description.id, self.processed_job.id, self.unprocessed_job.id]
        self.assertEqual(set(job_ids), set(expected_ids))
    
    def test_minimal_job_serialization(self):
        """Test serialization of job with minimal data"""
        minimal_job = JobDescription.objects.create(
            user=self.user,
            raw_content="Minimal content"
        )
        
        serializer = JobDescriptionListSerializer(minimal_job)
        data = serializer.data
        
        self.assertEqual(data['title'], '')
        self.assertEqual(data['company'], '')
        self.assertIsNone(data['location'])
        self.assertEqual(data['job_type'], 'unknown')
        self.assertFalse(data['is_processed'])
        self.assertTrue(data['is_active'])


class SerializerEdgeCasesTest(BaseSerializerTestCase):
    """Tests for edge cases and error conditions"""
    
    def test_job_description_serializer_with_none_values(self):
        """Test serialization when model fields are None"""
        job_with_nones = JobDescription.objects.create(
            user=self.user,
            raw_content="Content with nulls",
            location=None,
            salary_range=None,
            requirements=None,
            skills_required=None,
            experience_level=None,
            processing_notes=None
        )
        
        serializer = JobDescriptionSerializer(job_with_nones)
        data = serializer.data
        
        # Verify None values are properly serialized
        self.assertIsNone(data['location'])
        self.assertIsNone(data['salary_range'])
        self.assertIsNone(data['requirements'])
        self.assertIsNone(data['skills_required'])
        self.assertIsNone(data['experience_level'])
        self.assertIsNone(data['processing_notes'])
    
    def test_upload_serializer_with_malformed_filename(self):
        """Test upload with malformed filename"""
        # Test file with no extension
        no_ext_file = SimpleUploadedFile("noextension", b"content")
        data = {'document': no_ext_file}
        serializer = JobDescriptionUploadSerializer(data=data)
        
        self.assertFalse(serializer.is_valid())
        self.assertIn('Unsupported file type', str(serializer.errors))
    
    def test_upload_serializer_with_multiple_dots_filename(self):
        """Test upload with filename containing multiple dots"""
        multi_dot_file = SimpleUploadedFile("file.name.with.dots.pdf", b"content")
        data = {'document': multi_dot_file}
        serializer = JobDescriptionUploadSerializer(data=data)
        
        self.assertTrue(serializer.is_valid())  # Should use last extension
    
    def test_serializer_with_very_long_content(self):
        """Test serializers with very long content"""
        long_content = "Very long content " * 1000
        
        job = JobDescription.objects.create(
            user=self.user,
            raw_content=long_content,
            title="Long Job" * 10,
            company="Long Company" * 10
        )
        
        # Test that serialization works with long content
        serializer = JobDescriptionSerializer(job)
        data = serializer.data
        
        self.assertEqual(len(data['raw_content']), len(long_content))
    
    def test_serializer_with_unicode_content(self):
        """Test serializers with unicode content"""
        unicode_content = "Job with unicode: 中文, العربية, русский, 🎉"
        
        job = JobDescription.objects.create(
            user=self.user,
            raw_content=unicode_content,
            title="Unicode Job 🚀",
            company="International Corp 🌍"
        )
        
        serializer = JobDescriptionSerializer(job)
        data = serializer.data
        
        self.assertEqual(data['raw_content'], unicode_content)
        self.assertEqual(data['title'], "Unicode Job 🚀")
        self.assertEqual(data['company'], "International Corp 🌍")
    
    def test_concurrent_serialization(self):
        """Test that serializers work correctly with concurrent operations"""
        import threading
        
        results = []
        errors = []
        
        def serialize_job():
            try:
                serializer = JobDescriptionSerializer(self.job_description)
                results.append(serializer.data)
            except Exception as e:
                errors.append(e)
        
        # Create multiple threads
        threads = [threading.Thread(target=serialize_job) for _ in range(10)]
        
        # Start all threads
        for thread in threads:
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Verify results
        self.assertEqual(len(results), 10)
        self.assertEqual(len(errors), 0)
        
        # All results should be identical
        first_result = results[0]
        for result in results[1:]:
            self.assertEqual(result, first_result)


class SerializerIntegrationTest(BaseSerializerTestCase):
    """Integration tests combining multiple serializers"""
    
    @patch('jobs.serializers.extract_text_from_document')
    @patch('jobs.serializers.extract_job_details')
    def test_upload_then_list_then_detail_workflow(self, mock_extract_details, mock_extract_text):
        """Test complete workflow: upload -> list -> detail"""
        # Setup mocks
        mock_extract_text.return_value = "Extracted job content"
        mock_extract_details.return_value = {
            'title': 'Full Stack Developer',
            'company': 'StartupCorp',
            'location': 'San Francisco, CA',
            'job_type': 'full_time'
        }
        
        # 1. Upload job
        request = self.create_request_with_user()
        upload_data = {'raw_content': 'Original job posting'}
        upload_serializer = JobDescriptionUploadSerializer(
            data=upload_data,
            context={'request': request}
        )
        
        self.assertTrue(upload_serializer.is_valid())
        created_job = upload_serializer.save()
        
        # 2. List jobs (should include new job)
        jobs = JobDescription.objects.filter(user=self.user)
        list_serializer = JobDescriptionListSerializer(jobs, many=True)
        list_data = list_serializer.data
        
        # Find our created job in the list
        created_job_in_list = next(
            (item for item in list_data if item['id'] == created_job.id),
            None
        )
        self.assertIsNotNone(created_job_in_list)
        self.assertEqual(created_job_in_list['title'], 'Full Stack Developer')
        self.assertEqual(created_job_in_list['company'], 'StartupCorp')
        
        # 3. Get job details
        detail_serializer = JobDescriptionSerializer(created_job)
        detail_data = detail_serializer.data
        
        # Verify detail view has complete information
        self.assertEqual(detail_data['raw_content'], 'Original job posting')
        self.assertEqual(detail_data['title'], 'Full Stack Developer')
        self.assertEqual(detail_data['company'], 'StartupCorp')
        self.assertEqual(detail_data['location'], 'San Francisco, CA')
        self.assertEqual(detail_data['job_type'], 'full_time')
        self.assertTrue(detail_data['is_processed'])
    
    def test_serializer_consistency_across_operations(self):
        """Test that serializers maintain consistency across different operations"""
        # Create job using upload serializer
        request = self.create_request_with_user()
        upload_serializer = JobDescriptionUploadSerializer(
            data={'raw_content': 'Test job content'},
            context={'request': request}
        )
        
        self.assertTrue(upload_serializer.is_valid())
        job = upload_serializer.save()
        
        # Serialize using detail serializer
        detail_serializer = JobDescriptionSerializer(job)
        detail_data = detail_serializer.data
        
        # Serialize using list serializer
        list_serializer = JobDescriptionListSerializer(job)
        list_data = list_serializer.data
        
        # Verify consistent fields between serializers
        common_fields = ['id', 'title', 'company', 'location', 'job_type', 'is_processed', 'is_active']
        for field in common_fields:
            self.assertEqual(
                detail_data[field], 
                list_data[field],
                f"Field '{field}' differs between detail and list serializers"
            )


class SerializerPerformanceTest(BaseSerializerTestCase):
    """Performance tests for serializers"""
    
    def test_bulk_serialization_performance(self):
        """Test serializer performance with large datasets"""
        import time
        
        # Create many job descriptions
        jobs = []
        for i in range(100):
            jobs.append(JobDescription(
                user=self.user,
                raw_content=f"Job description {i}",
                title=f"Job Title {i}",
                company=f"Company {i}",
                is_processed=True
            ))
        
        JobDescription.objects.bulk_create(jobs)
        
        # Test list serializer performance
        start_time = time.time()
        all_jobs = JobDescription.objects.filter(user=self.user)
        serializer = JobDescriptionListSerializer(all_jobs, many=True)
        data = serializer.data
        end_time = time.time()
        
        # Verify results
        self.assertGreaterEqual(len(data), 100)  # At least 100 jobs (plus setUp jobs)
        
        # Performance should be reasonable (less than 1 second for 100 jobs)
        serialization_time = end_time - start_time
        self.assertLess(serialization_time, 1.0, "Serialization took too long")
    
    def test_deep_nesting_serialization(self):
        """Test serialization with deeply nested or complex data"""
        complex_content = {
            'nested': {
                'level1': {
                    'level2': {
                        'data': 'deep value'
                    }
                }
            }
        }
        
        job = JobDescription.objects.create(
            user=self.user,
            raw_content=str(complex_content),
            requirements="Complex requirements with nested data structures",
            skills_required="Advanced skills in data manipulation"
        )
        
        serializer = JobDescriptionSerializer(job)
        data = serializer.data
        
        # Should handle complex content without issues
        self.assertIn('nested', data['raw_content'])
        self.assertEqual(data['requirements'], "Complex requirements with nested data structures")


class SerializerSecurityTest(BaseSerializerTestCase):
    """Security-related tests for serializers"""
    
    def test_user_isolation_in_serialization(self):
        """Test that serializers respect user boundaries"""
        other_user_job = JobDescription.objects.create(
            user=self.other_user,
            raw_content="Other user's job",
            title="Secret Job",
            company="Private Company"
        )
        
        # Serialize current user's job - should work
        serializer = JobDescriptionSerializer(self.job_description)
        data = serializer.data
        self.assertEqual(data['user'], str(self.user))
        
        # Serialize other user's job - should still work but show different user
        other_serializer = JobDescriptionSerializer(other_user_job)
        other_data = other_serializer.data
        self.assertEqual(other_data['user'], str(self.other_user))
        self.assertNotEqual(other_data['user'], str(self.user))
    
    def test_malicious_filename_handling(self):
        """Test handling of potentially malicious filenames"""
        malicious_filenames = [
            '../../../etc/passwd.txt',
            '..\\..\\windows\\system32\\config.txt',
            'normal_file.pdf',
            '/absolute/path/file.docx',
            'file with spaces.doc',
            'файл.pdf',  # Unicode filename
        ]
        
        for filename in malicious_filenames:
            if filename.endswith(('.txt', '.pdf', '.docx', '.doc')):
                test_file = SimpleUploadedFile(filename, b"content")
                data = {'document': test_file}
                serializer = JobDescriptionUploadSerializer(data=data)
                
                # Should validate successfully (filename sanitization is handled elsewhere)
                self.assertTrue(serializer.is_valid(), f"Failed for filename: {filename}")
    
    def test_xss_content_handling(self):
        """Test that serializers don't execute potentially malicious content"""
        xss_content = "<script>alert('xss')</script>"
        
        job = JobDescription.objects.create(
            user=self.user,
            raw_content=xss_content,
            title="<img src=x onerror=alert(1)>",
            company="</script><script>alert('company')</script>"
        )
        
        serializer = JobDescriptionSerializer(job)
        data = serializer.data
        
        # Content should be preserved as-is (sanitization happens in views/frontend)
        self.assertEqual(data['raw_content'], xss_content)
        self.assertEqual(data['title'], "<img src=x onerror=alert(1)>")
        self.assertEqual(data['company'], "</script><script>alert('company')</script>")
    
    def test_sql_injection_content_handling(self):
        """Test handling of SQL injection attempts in content"""
        sql_injection_content = "'; DROP TABLE jobs_jobdescription; --"
        
        job = JobDescription.objects.create(
            user=self.user,
            raw_content=sql_injection_content,
            title="Robert'; DROP TABLE students; --"
        )
        
        serializer = JobDescriptionSerializer(job)
        data = serializer.data
        
        # Content should be preserved (Django ORM handles SQL injection prevention)
        self.assertEqual(data['raw_content'], sql_injection_content)
        self.assertEqual(data['title'], "Robert'; DROP TABLE students; --")


class SerializerValidationTest(BaseSerializerTestCase):
    """Additional validation tests"""
    
    def test_upload_serializer_custom_validation_logic(self):
        """Test custom validation logic in upload serializer"""
        # Test with document but no raw content
        data = {'document': self.create_test_file('test.pdf', 'content')}
        serializer = JobDescriptionUploadSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        
        # Test with raw content but no document
        data = {'raw_content': 'Just text content'}
        serializer = JobDescriptionUploadSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        
        # Test with both
        data = {
            'document': self.create_test_file('test.pdf', 'content'),
            'raw_content': 'Additional text'
        }
        serializer = JobDescriptionUploadSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        
        # Test with neither
        data = {}
        serializer = JobDescriptionUploadSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        
        # Test with empty strings/whitespace
        data = {'raw_content': '   \n\t   '}
        serializer = JobDescriptionUploadSerializer(data=data)
        self.assertFalse(serializer.is_valid())
    
    def test_file_extension_case_sensitivity(self):
        """Test that file extension validation is case insensitive"""
        extensions_to_test = [
            ('test.PDF', True),
            ('test.Pdf', True),
            ('test.pDf', True),
            ('test.DOCX', True),
            ('test.Doc', True),
            ('test.TXT', True),
            ('test.EXE', False),
            ('test.JPG', False),
        ]
        
        for filename, should_be_valid in extensions_to_test:
            test_file = SimpleUploadedFile(filename, b"content")
            data = {'document': test_file}
            serializer = JobDescriptionUploadSerializer(data=data)
            
            if should_be_valid:
                self.assertTrue(serializer.is_valid(), f"Should be valid: {filename}")
            else:
                self.assertFalse(serializer.is_valid(), f"Should be invalid: {filename}")
    
    def test_serializer_partial_updates(self):
        """Test partial updates with JobDescriptionSerializer"""
        # Test updating single field
        serializer = JobDescriptionSerializer(
            self.job_description,
            data={'title': 'Updated Title'},
            partial=True
        )
        self.assertTrue(serializer.is_valid())
        updated_job = serializer.save()
        self.assertEqual(updated_job.title, 'Updated Title')
        self.assertEqual(updated_job.company, 'TechCorp')  # Unchanged
        
        # Test updating multiple fields
        serializer = JobDescriptionSerializer(
            self.job_description,
            data={
                'title': 'Another Update',
                'location': 'San Francisco, CA',
                'job_type': 'remote'
            },
            partial=True
        )
        self.assertTrue(serializer.is_valid())
        updated_job = serializer.save()
        self.assertEqual(updated_job.title, 'Another Update')
        self.assertEqual(updated_job.location, 'San Francisco, CA')
        self.assertEqual(updated_job.job_type, 'remote')
    
    def test_serializer_invalid_choice_fields(self):
        """Test validation of choice fields"""
        # Test invalid job_type
        serializer = JobDescriptionSerializer(
            self.job_description,
            data={'job_type': 'invalid_type'},
            partial=True
        )
        self.assertFalse(serializer.is_valid())
        self.assertIn('job_type', serializer.errors)
        
        # Test valid job_type
        valid_types = ['full_time', 'part_time', 'contract', 'internship', 'remote', 'unknown']
        for job_type in valid_types:
            serializer = JobDescriptionSerializer(
                self.job_description,
                data={'job_type': job_type},
                partial=True
            )
            self.assertTrue(serializer.is_valid(), f"Failed for job_type: {job_type}")


class SerializerErrorHandlingTest(BaseSerializerTestCase):
    """Test error handling in serializers"""
    
    @patch('jobs.serializers.extract_text_from_document')
    def test_document_processing_various_errors(self, mock_extract_text):
        """Test handling of various document processing errors"""
        error_scenarios = [
            ValueError("Unsupported file format"),
            IOError("File not found"),
            Exception("Generic processing error"),
            UnicodeDecodeError('utf-8', b'', 0, 1, 'invalid start byte'),
        ]
        
        for error in error_scenarios:
            mock_extract_text.side_effect = error
            
            request = self.create_request_with_user()
            serializer = JobDescriptionUploadSerializer(
                data={'document': self.create_test_file('test.pdf', 'content')},
                context={'request': request}
            )
            
            self.assertTrue(serializer.is_valid())
            
            with self.assertRaises(Exception) as context:
                serializer.save()
            
            self.assertIn("Document processing error", str(context.exception))
    
    @patch('jobs.serializers.extract_job_details')
    def test_job_details_extraction_various_errors(self, mock_extract_details):
        """Test handling of various job details extraction errors"""
        error_scenarios = [
            KeyError("Missing key"),
            AttributeError("Attribute not found"),
            TypeError("Type error"),
            Exception("Generic extraction error"),
        ]
        
        for error in error_scenarios:
            mock_extract_details.side_effect = error
            
            request = self.create_request_with_user()
            serializer = JobDescriptionUploadSerializer(
                data={'raw_content': 'Test content'},
                context={'request': request}
            )
            
            self.assertTrue(serializer.is_valid())
            job = serializer.save()
            
            # Should create job but mark as unprocessed
            self.assertFalse(job.is_processed)
            self.assertIn("Error extracting details", job.processing_notes)


class SerializerFieldTest(BaseSerializerTestCase):
    """Test individual serializer fields"""
    
    def test_string_related_field_user(self):
        """Test StringRelatedField for user"""
        serializer = JobDescriptionSerializer()
        user_field = serializer.fields['user']
        
        # Should be read-only
        self.assertTrue(user_field.read_only)
        
        # Test representation
        self.assertEqual(str(self.user), user_field.to_representation(self.user))
    
    def test_datetime_fields_read_only(self):
        """Test that datetime fields are read-only"""
        serializer = JobDescriptionSerializer()
        
        created_at_field = serializer.fields['created_at']
        updated_at_field = serializer.fields['updated_at']
        
        self.assertTrue(created_at_field.read_only)
        self.assertTrue(updated_at_field.read_only)
    
    def test_serializer_method_field_document_name(self):
        """Test SerializerMethodField for document_name"""
        serializer = JobDescriptionSerializer()
        document_name_field = serializer.fields['document_name']
        
        # Should be read-only (SerializerMethodField is always read-only)
        self.assertTrue(document_name_field.read_only)
        
        # Test the method exists
        self.assertTrue(hasattr(serializer, 'get_document_name'))
    
    def test_file_field_configuration(self):
        """Test FileField configuration in upload serializer"""
        serializer = JobDescriptionUploadSerializer()
        document_field = serializer.fields['document']
        
        self.assertFalse(document_field.required)
        self.assertTrue(document_field.allow_null)


# Additional utility tests
class SerializerUtilityMethodTest(BaseSerializerTestCase):
    """Test utility methods in serializers"""
    
    def test_document_name_edge_cases(self):
        """Test document name extraction edge cases"""
        serializer = JobDescriptionSerializer()
        
        # Test cases for get_document_name
        test_cases = [
            # (document.name, expected_result)
            ('simple.pdf', 'simple.pdf'),
            ('path/to/file.docx', 'file.docx'),
            ('deep/nested/path/document.txt', 'document.txt'),
            ('file_without_extension', 'file_without_extension'),
            ('', ''),
            ('folder/', ''),
            ('/absolute/path/file.pdf', 'file.pdf'),
            ('\\windows\\path\\file.doc', 'file.doc'),
        ]
        
        for document_name, expected in test_cases:
            mock_obj = Mock()
            mock_obj.document = Mock()
            mock_obj.document.name = document_name
            
            result = serializer.get_document_name(mock_obj)
            self.assertEqual(result, expected, f"Failed for: {document_name}")
