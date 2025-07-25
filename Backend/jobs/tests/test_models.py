import tempfile
from unittest.mock import patch
from django.test import  override_settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils import timezone
from django.db.utils import IntegrityError
from datetime import datetime
from jobs.models import JobDescription, job_document_upload_path
from rest_framework.test import APITestCase
from django.test import TransactionTestCase
from django.db import transaction
User = get_user_model()


class BaseSerializerTestCase(APITestCase):
    """Base mixin providing common test utilities and data"""
    
    @classmethod
    def setUp(self):
        """Set up test users"""
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
    
    def create_sample_job(self, user=None, **kwargs):
        """Create a sample job description with default or custom values"""
        defaults = {
            'user': user or self.user1,
            'raw_content': 'Software Engineer position at Tech Corp. We are looking for an experienced developer...',
            'title': 'Software Engineer',
            'company': 'Tech Corp',
            'location': 'San Francisco, CA',
            'job_type': 'full_time',
            'salary_range': '$100,000 - $150,000',
            'requirements': 'Bachelor degree in Computer Science, 3+ years experience',
            'skills_required': 'Python, Django, REST APIs, PostgreSQL',
            'experience_level': '3-5 years',
            'is_processed': True,
            'processing_notes': 'Successfully processed job description'
        }
        defaults.update(kwargs)
        return JobDescription.objects.create(**defaults)
    
    def create_test_file(self, content=b'test document content', filename='test_document.pdf'):
        """Create a test file for upload testing"""
        return SimpleUploadedFile(
            filename, 
            content, 
            content_type='application/pdf'
        )
    
    def create_minimal_job(self, user=None, **kwargs):
        """Create a job with only required fields"""
        defaults = {
            'user': user or self.user1,
            'raw_content': 'Minimal job description content'
        }
        defaults.update(kwargs)
        return JobDescription.objects.create(**defaults)


class JobDescriptionModelCreationTests( BaseSerializerTestCase):
    """Test JobDescription model creation with various scenarios"""
    
    def test_create_job_with_all_fields(self):
        """Test creating a job with all fields populated"""
        job = self.create_sample_job()
        
        # Test all field assignments
        self.assertEqual(job.user, self.user1)
        self.assertEqual(job.raw_content, 'Software Engineer position at Tech Corp. We are looking for an experienced developer...')
        self.assertEqual(job.title, 'Software Engineer')
        self.assertEqual(job.company, 'Tech Corp')
        self.assertEqual(job.location, 'San Francisco, CA')
        self.assertEqual(job.job_type, 'full_time')
        self.assertEqual(job.salary_range, '$100,000 - $150,000')
        self.assertEqual(job.requirements, 'Bachelor degree in Computer Science, 3+ years experience')
        self.assertEqual(job.skills_required, 'Python, Django, REST APIs, PostgreSQL')
        self.assertEqual(job.experience_level, '3-5 years')
        self.assertTrue(job.is_processed)
        self.assertEqual(job.processing_notes, 'Successfully processed job description')
        self.assertTrue(job.is_active)
        
        # Test auto-generated fields
        self.assertIsNotNone(job.id)
        self.assertIsNotNone(job.created_at)
        self.assertIsNotNone(job.updated_at)
        self.assertIsInstance(job.created_at, datetime)
        self.assertIsInstance(job.updated_at, datetime)
    
    def test_create_job_minimal_required_fields(self):
        """Test creating a job with only required fields"""
        job = self.create_minimal_job()
        
        # Required fields
        self.assertEqual(job.user, self.user1)
        self.assertEqual(job.raw_content, 'Minimal job description content')
        
        # Default values
        self.assertEqual(job.job_type, 'unknown')
        self.assertFalse(job.is_processed)
        self.assertTrue(job.is_active)
        
        # Optional fields should be empty/None
        self.assertEqual(job.title, '')
        self.assertEqual(job.company, '')
        self.assertIsNone(job.location)
        self.assertIsNone(job.salary_range)
        self.assertIsNone(job.requirements)
        self.assertIsNone(job.skills_required)
        self.assertIsNone(job.experience_level)
        self.assertIsNone(job.processing_notes)
        self.assertFalse(job.document)
    
    def test_create_job_with_document(self):
        """Test creating a job with a document file"""
        test_file = self.create_test_file(b'Sample resume content', 'resume.pdf')
        
        job = JobDescription.objects.create(
            user=self.user1,
            raw_content='Job with document',
            document=test_file,
            title='Document Job'
        )
        
        self.assertTrue(job.document)
        self.assertIn('resume.pdf', job.document.name)
        self.assertEqual(job.title, 'Document Job')
    
    def test_create_multiple_jobs_same_user(self):
        """Test creating multiple jobs for the same user"""
        job1 = self.create_sample_job(title='First Job')
        job2 = self.create_sample_job(title='Second Job')
        job3 = self.create_sample_job(title='Third Job')
        
        # All jobs should be created successfully
        self.assertEqual(JobDescription.objects.count(), 3)
        self.assertEqual(job1.user, self.user1)
        self.assertEqual(job2.user, self.user1)
        self.assertEqual(job3.user, self.user1)
        
        # All should have different IDs
        self.assertNotEqual(job1.id, job2.id)
        self.assertNotEqual(job2.id, job3.id)
        self.assertNotEqual(job1.id, job3.id)
    
    def test_create_jobs_different_users(self):
        """Test creating jobs for different users"""
        job1 = self.create_sample_job(user=self.user1, title='User1 Job')
        job2 = self.create_sample_job(user=self.user2, title='User2 Job')
        
        self.assertEqual(job1.user, self.user1)
        self.assertEqual(job2.user, self.user2)
        self.assertNotEqual(job1.user, job2.user)
        
        # Test user relationship
        user1_jobs = self.user1.job_descriptions.all()
        user2_jobs = self.user2.job_descriptions.all()
        
        self.assertIn(job1, user1_jobs)
        self.assertNotIn(job1, user2_jobs)
        self.assertIn(job2, user2_jobs)
        self.assertNotIn(job2, user1_jobs)
    
    def test_user_foreign_key_constraint(self):
        """Test that user field is required (foreign key constraint)"""
        with self.assertRaises(IntegrityError):
            JobDescription.objects.create(
                user=None,
                raw_content='Job without user'
            )


class JobDescriptionModelFieldTests( BaseSerializerTestCase):
    """Test JobDescription model field behaviors and constraints"""
    
    def test_job_type_choices(self):
        """Test all valid job type choices"""
        job_types = [
            ('full_time', 'Full Time'),
            ('part_time', 'Part Time'),
            ('contract', 'Contract'),
            ('internship', 'Internship'),
            ('remote', 'Remote'),
            ('unknown', 'Unknown'),
        ]
        
        for job_type_value, job_type_display in job_types:
            job = self.create_sample_job(job_type=job_type_value)
            self.assertEqual(job.job_type, job_type_value)
            self.assertEqual(job.get_job_type_display(), job_type_display)
    
    def test_job_type_default_value(self):
        """Test that job_type defaults to 'unknown'"""
        job = self.create_minimal_job()
        self.assertEqual(job.job_type, 'unknown')
        self.assertEqual(job.get_job_type_display(), 'Unknown')
    
    def test_boolean_field_defaults(self):
        """Test boolean field default values"""
        job = self.create_minimal_job()
        
        self.assertFalse(job.is_processed)  # Default False
        self.assertTrue(job.is_active)      # Default True
        self.assertIsInstance(job.is_processed, bool)
        self.assertIsInstance(job.is_active, bool)
    
    def test_nullable_fields(self):
        """Test that nullable fields can be None"""
        job = JobDescription.objects.create(
            user=self.user1,
            raw_content='Test job',
            location=None,
            salary_range=None,
            requirements=None,
            skills_required=None,
            experience_level=None,
            processing_notes=None,
            document=None
        )
        
        # These fields should accept None
        self.assertIsNone(job.location)
        self.assertIsNone(job.salary_range)
        self.assertIsNone(job.requirements)
        self.assertIsNone(job.skills_required)
        self.assertIsNone(job.experience_level)
        self.assertIsNone(job.processing_notes)
        self.assertIsNone(job.document.name if job.document else None)
    
    def test_blank_fields(self):
        """Test that fields can be blank strings"""
        job = JobDescription.objects.create(
            user=self.user1,
            raw_content='Test job',
            title='',
            company='',
            location='',
            salary_range='',
            requirements='',
            skills_required='',
            experience_level='',
            processing_notes=''
        )
        
        self.assertEqual(job.title, '')
        self.assertEqual(job.company, '')
        self.assertEqual(job.location, '')
        self.assertEqual(job.salary_range, '')
        self.assertEqual(job.requirements, '')
        self.assertEqual(job.skills_required, '')
        self.assertEqual(job.experience_level, '')
        self.assertEqual(job.processing_notes, '')
    
    def test_max_length_constraints(self):
        """Test field max_length constraints"""
        # Test fields with 200 char limit
        char_200_fields = ['title', 'company', 'location']
        
        for field_name in char_200_fields:
            # Test exact max length (should work)
            exact_200 = 'A' * 200
            kwargs = {field_name: exact_200}
            job = self.create_sample_job(**kwargs)
            self.assertEqual(len(getattr(job, field_name)), 200)
        
        # Test salary_range (100 char limit)
        exact_100 = 'B' * 100
        job = self.create_sample_job(salary_range=exact_100)
        self.assertEqual(len(job.salary_range), 100)
        
        # Test experience_level (100 char limit)
        job = self.create_sample_job(experience_level=exact_100)
        self.assertEqual(len(job.experience_level), 100)
    
    def test_text_fields_unlimited_length(self):
        """Test that TextField fields can handle large amounts of text"""
        large_text = 'A' * 10000  # 10KB of text
        
        job = self.create_sample_job(
            raw_content=large_text,
            requirements=large_text,
            skills_required=large_text,
            processing_notes=large_text
        )
        
        self.assertEqual(len(job.raw_content), 10000)
        self.assertEqual(len(job.requirements), 10000)
        self.assertEqual(len(job.skills_required), 10000)
        self.assertEqual(len(job.processing_notes), 10000)


class JobDescriptionModelMethodTests( BaseSerializerTestCase):
    """Test JobDescription model methods"""
    
    def test_string_representation_with_title_and_company(self):
        """Test __str__ method when both title and company are present"""
        job = self.create_sample_job(
            title='Senior Python Developer',
            company='Amazing Tech Inc'
        )
        
        expected = 'Senior Python Developer at Amazing Tech Inc'
        self.assertEqual(str(job), expected)
    
    def test_string_representation_with_title_only(self):
        """Test __str__ method when only title is present"""
        job = self.create_sample_job(
            title='Data Scientist',
            company=''
        )
        
        expected = f'Job #{job.id}'
        self.assertEqual(str(job), expected)
    
    def test_string_representation_with_company_only(self):
        """Test __str__ method when only company is present"""
        job = self.create_sample_job(
            title='',
            company='Google'
        )
        
        expected = f'Job #{job.id}'
        self.assertEqual(str(job), expected)
    
    def test_string_representation_without_title_and_company(self):
        """Test __str__ method when neither title nor company are present"""
        job = self.create_minimal_job()
        
        expected = f'Job #{job.id}'
        self.assertEqual(str(job), expected)
    
    
    def test_string_representation_with_whitespace_only(self):
        """Test __str__ method when title/company contain only whitespace"""
        job = self.create_sample_job(
            title='   ',
            company='   '
        )
        
        # Whitespace-only strings should be treated as empty
        expected = f'Job #{job.id}'
        self.assertEqual(str(job), expected)


class JobDescriptionModelSaveMethodTests( BaseSerializerTestCase):
    """Test JobDescription model save method behaviors"""
    
    def test_field_truncation_on_save(self):
        """Test that long field values are truncated to max_length on save"""
        # Create strings longer than max_length
        long_title = 'A' * 250      # title max_length = 200
        long_company = 'B' * 250    # company max_length = 200
        long_location = 'C' * 250   # location max_length = 200
        
        job = JobDescription.objects.create(
            user=self.user1,
            raw_content='Test job with long fields',
            title=long_title,
            company=long_company,
            location=long_location
        )
        
        # Fields should be truncated
        self.assertEqual(len(job.title), 200)
        self.assertEqual(len(job.company), 200)
        self.assertEqual(len(job.location), 200)
        
        # Content should be truncated properly
        self.assertEqual(job.title, 'A' * 200)
        self.assertEqual(job.company, 'B' * 200)
        self.assertEqual(job.location, 'C' * 200)
    
    def test_field_truncation_on_update(self):
        """Test that field truncation works on updates too"""
        job = self.create_sample_job()
        
        # Update with long values
        job.title = 'X' * 300
        job.company = 'Y' * 300
        job.location = 'Z' * 300
        job.save()
        
        job.refresh_from_db()
        self.assertEqual(len(job.title), 200)
        self.assertEqual(len(job.company), 200)
        self.assertEqual(len(job.location), 200)
    
    def test_updated_at_automatic_update(self):
        """Test that updated_at is automatically updated on save"""
        job = self.create_sample_job()
        original_updated_at = job.updated_at
        
        # Add small delay to ensure timestamp difference
        import time
        time.sleep(0.01)
        
        # Update the job
        job.title = 'Updated Title'
        job.save()
        
        job.refresh_from_db()
        self.assertGreater(job.updated_at, original_updated_at)
    
    def test_created_at_not_changed_on_update(self):
        """Test that created_at doesn't change on updates"""
        job = self.create_sample_job()
        original_created_at = job.created_at
        
        # Update the job
        job.title = 'Updated Title'
        job.save()
        
        job.refresh_from_db()
        self.assertEqual(job.created_at, original_created_at)

    def test_save_preserves_other_fields(self):
        """Test that save method doesn't affect other fields during truncation"""
        job = self.create_sample_job(
            title='A' * 250,  # Will be truncated
            raw_content='Original content',
            job_type='contract',
            is_processed=False
        )
        
        # These fields should be preserved
        self.assertEqual(job.raw_content, 'Original content')
        self.assertEqual(job.job_type, 'contract')
        self.assertFalse(job.is_processed)
        
        # Only title should be truncated
        self.assertEqual(len(job.title), 200)


class JobDescriptionModelDeleteTests( BaseSerializerTestCase):
    """Test JobDescription model delete method and cascading"""
    
    @override_settings(MEDIA_ROOT=tempfile.mkdtemp())
    def test_delete_job_without_document(self):
        """Test deleting a job without a document"""
        job = self.create_sample_job()
        job_id = job.id
        
        # Delete should work normally
        job.delete()
        
        # Job should be gone
        self.assertFalse(JobDescription.objects.filter(id=job_id).exists())
    
    @override_settings(MEDIA_ROOT=tempfile.mkdtemp())
    def test_delete_job_with_document_file_exists(self):
        """Test deleting a job with a document when file exists"""
        test_file = self.create_test_file(b'document content', 'test_resume.pdf')
        
        job = JobDescription.objects.create(
            user=self.user1,
            raw_content='Job with document',
            document=test_file
        )
        
        with patch('os.path.isfile') as mock_isfile, \
             patch('os.remove') as mock_remove:
            
            mock_isfile.return_value = True
            
            job.delete()
            
            # Should check if file exists and remove it
            mock_isfile.assert_called_once()
            mock_remove.assert_called_once()
    
    @override_settings(MEDIA_ROOT=tempfile.mkdtemp())
    def test_delete_job_with_document_file_not_exists(self):
        """Test deleting a job with a document when file doesn't exist"""
        test_file = self.create_test_file(b'document content', 'missing_file.pdf')
        
        job = JobDescription.objects.create(
            user=self.user1,
            raw_content='Job with missing document',
            document=test_file
        )
        
        with patch('os.path.isfile') as mock_isfile, \
             patch('os.remove') as mock_remove:
            
            mock_isfile.return_value = False
            
            job.delete()
            
            # Should check if file exists but not try to remove it
            mock_isfile.assert_called_once()
            mock_remove.assert_not_called()
    
    @override_settings(MEDIA_ROOT=tempfile.mkdtemp())
    def test_delete_job_with_document_os_error(self):
        """Test deleting a job when file removal fails"""
        test_file = self.create_test_file(b'document content', 'protected_file.pdf')
        
        job = JobDescription.objects.create(
            user=self.user1,
            raw_content='Job with protected document',
            document=test_file
        )
        
        with patch('os.path.isfile') as mock_isfile, \
             patch('os.remove') as mock_remove:
            
            mock_isfile.return_value = True
            mock_remove.side_effect = OSError('Permission denied')
            
            # Delete should still work even if file removal fails
            job.delete()
            
            mock_isfile.assert_called_once()
            mock_remove.assert_called_once()
    
    def test_cascade_delete_when_user_deleted(self):
        """Test that jobs are deleted when user is deleted"""
        job1 = self.create_sample_job(user=self.user1)
        job2 = self.create_sample_job(user=self.user1)
        job3 = self.create_sample_job(user=self.user2)
        
        self.user1.id
        
        # Delete user1
        self.user1.delete()
        
        # user1's jobs should be deleted
        self.assertFalse(JobDescription.objects.filter(id=job1.id).exists())
        self.assertFalse(JobDescription.objects.filter(id=job2.id).exists())
        
        # user2's job should still exist
        self.assertTrue(JobDescription.objects.filter(id=job3.id).exists())
        self.assertEqual(job3.user, self.user2)


class JobDescriptionModelOrderingTests( BaseSerializerTestCase):
    """Test JobDescription model ordering"""
    
    def test_default_ordering_by_created_at_desc(self):
        """Test that jobs are ordered by created_at descending by default"""
        # Create jobs with slight delays to ensure different timestamps
        job1 = self.create_sample_job(title='First Job')
        
        import time
        time.sleep(0.01)
        job2 = self.create_sample_job(title='Second Job')
        
        time.sleep(0.01)
        job3 = self.create_sample_job(title='Third Job')
        
        # Get all jobs (should be ordered by created_at desc)
        jobs = list(JobDescription.objects.all())
        
        # Most recent first
        self.assertEqual(jobs[0], job3)
        self.assertEqual(jobs[1], job2)
        self.assertEqual(jobs[2], job1)
        
        # Verify timestamps are in descending order
        self.assertGreaterEqual(jobs[0].created_at, jobs[1].created_at)
        self.assertGreaterEqual(jobs[1].created_at, jobs[2].created_at)
    
    def test_ordering_with_multiple_users(self):
        """Test ordering works correctly across multiple users"""
        self.create_sample_job(user=self.user1, title='User1 Job1')
        self.create_sample_job(user=self.user2, title='User2 Job1')
        self.create_sample_job(user=self.user1, title='User1 Job2')
        
        all_jobs = list(JobDescription.objects.all())
        
        # Should be ordered by created_at desc regardless of user
        self.assertEqual(len(all_jobs), 3)
        # Most recent should be first
        self.assertGreaterEqual(all_jobs[0].created_at, all_jobs[1].created_at)
        self.assertGreaterEqual(all_jobs[1].created_at, all_jobs[2].created_at)


class JobDescriptionModelMetaTests( BaseSerializerTestCase):
    """Test JobDescription model Meta configurations"""
    
    def test_verbose_name(self):
        """Test model verbose name"""
        self.assertEqual(JobDescription._meta.verbose_name, 'Job Description')
    
    def test_verbose_name_plural(self):
        """Test model verbose name plural"""
        self.assertEqual(JobDescription._meta.verbose_name_plural, 'Job Descriptions')
    
    def test_ordering_configuration(self):
        """Test that ordering is configured correctly in Meta"""
        self.assertEqual(JobDescription._meta.ordering, ['-created_at'])


class JobDocumentUploadPathTests( BaseSerializerTestCase):
    """Test job_document_upload_path function"""
    
    def test_upload_path_generation(self):
        """Test that upload path is generated correctly"""
        job = JobDescription(user=self.user1)
        filename = 'my_resume.pdf'
        
        path = job_document_upload_path(job, filename)
        expected_path = f'job_documents/{self.user1.id}/my_resume.pdf'
        
        self.assertEqual(path, expected_path)
    
    def test_upload_path_with_different_users(self):
        """Test upload path generation for different users"""
        job1 = JobDescription(user=self.user1)
        job2 = JobDescription(user=self.user2)
        filename = 'document.pdf'
        
        path1 = job_document_upload_path(job1, filename)
        path2 = job_document_upload_path(job2, filename)
        
        expected_path1 = f'job_documents/{self.user1.id}/document.pdf'
        expected_path2 = f'job_documents/{self.user2.id}/document.pdf'
        
        self.assertEqual(path1, expected_path1)
        self.assertEqual(path2, expected_path2)
        self.assertNotEqual(path1, path2)
    
    def test_upload_path_with_special_characters(self):
        """Test upload path with filenames containing special characters"""
        job = JobDescription(user=self.user1)
        filenames = [
            'résumé with spaces.pdf',
            'document-with-dashes.docx',
            'file_with_underscores.txt',
            'document (1).pdf'
        ]
        
        for filename in filenames:
            path = job_document_upload_path(job, filename)
            expected_path = f'job_documents/{self.user1.id}/{filename}'
            self.assertEqual(path, expected_path)


class JobDescriptionModelFieldValidationTests( BaseSerializerTestCase):
    """Test field validation and constraints"""
    
    def test_required_fields(self):
        """Test that required fields are enforced"""
        
        # Missing both user + raw_content
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                JobDescription.objects.create()
        
        # Missing only raw_content
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                JobDescription.objects.create(user=self.user1, raw_content=None)
        
        # Missing only user
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                JobDescription.objects.create(raw_content='Test content')


    def test_help_text_attributes(self):
        """Test that help text is set correctly on fields"""
        raw_content_field = JobDescription._meta.get_field('raw_content')
        document_field = JobDescription._meta.get_field('document')
        
        self.assertEqual(raw_content_field.help_text, 'Original job description content')
        self.assertEqual(document_field.help_text, 'Optional: Upload job description document')
    
    def test_field_attributes(self):
        """Test various field attributes are set correctly"""
        # Test CharField attributes
        title_field = JobDescription._meta.get_field('title')
        self.assertEqual(title_field.max_length, 200)
        self.assertTrue(title_field.blank)
        
        company_field = JobDescription._meta.get_field('company')
        self.assertEqual(company_field.max_length, 200)
        self.assertTrue(company_field.blank)
        
        # Test nullable fields
        location_field = JobDescription._meta.get_field('location')
        self.assertTrue(location_field.null)
        self.assertTrue(location_field.blank)
        
        # Test TextField attributes
        raw_content_field = JobDescription._meta.get_field('raw_content')
        self.assertFalse(raw_content_field.blank)
        self.assertFalse(raw_content_field.null)
        
        # Test BooleanField defaults
        is_processed_field = JobDescription._meta.get_field('is_processed')
        self.assertFalse(is_processed_field.default)
        
        is_active_field = JobDescription._meta.get_field('is_active')
        self.assertTrue(is_active_field.default)
    
    def test_choice_field_validation(self):
        """Test that choice fields only accept valid choices"""
        valid_choices = ['full_time', 'part_time', 'contract', 'internship', 'remote', 'unknown']
        
        for choice in valid_choices:
            job = self.create_sample_job(job_type=choice)
            self.assertEqual(job.job_type, choice)
        
        # Invalid choice should work at model level (validation happens at form/serializer level)
        job = self.create_sample_job(job_type='invalid_choice')
        self.assertEqual(job.job_type, 'invalid_choice')


class JobDescriptionModelRelationshipTests( BaseSerializerTestCase):
    """Test model relationships and related managers"""
    
    def test_user_foreign_key_relationship(self):
        """Test the user foreign key relationship"""
        job = self.create_sample_job()
        
        # Forward relationship
        self.assertEqual(job.user, self.user1)
        self.assertIsInstance(job.user, User)
    
    def test_reverse_relationship_related_name(self):
        """Test the reverse relationship using related_name"""
        job1 = self.create_sample_job(user=self.user1, title='Job 1')
        job2 = self.create_sample_job(user=self.user1, title='Job 2')
        job3 = self.create_sample_job(user=self.user2, title='Job 3')
        
        # Test user1's jobs
        user1_jobs = self.user1.job_descriptions.all()
        self.assertEqual(user1_jobs.count(), 2)
        self.assertIn(job1, user1_jobs)
        self.assertIn(job2, user1_jobs)
        self.assertNotIn(job3, user1_jobs)
        
        # Test user2's jobs
        user2_jobs = self.user2.job_descriptions.all()
        self.assertEqual(user2_jobs.count(), 1)
        self.assertIn(job3, user2_jobs)
        self.assertNotIn(job1, user2_jobs)
        self.assertNotIn(job2, user2_jobs)
    
    def test_cascade_delete_relationship(self):
        """Test CASCADE delete behavior"""
        job = self.create_sample_job()
        job_id = job.id
        
        # Delete user should cascade delete job
        self.user1.delete()
        
        self.assertFalse(JobDescription.objects.filter(id=job_id).exists())
    
    def test_related_manager_methods(self):
        """Test related manager methods"""
        job1 = self.create_sample_job(user=self.user1, is_processed=True)
        self.create_sample_job(user=self.user1, is_processed=False)
        
        # Test filtering through related manager
        processed_jobs = self.user1.job_descriptions.filter(is_processed=True)
        self.assertEqual(processed_jobs.count(), 1)
        self.assertEqual(processed_jobs.first(), job1)
        
        # Test creation through related manager
        new_job = self.user1.job_descriptions.create(
            raw_content='Created through related manager',
            title='Related Manager Job'
        )
        
        self.assertEqual(new_job.user, self.user1)
        self.assertEqual(self.user1.job_descriptions.count(), 3)


class JobDescriptionModelTimestampTests( BaseSerializerTestCase):
    """Test timestamp field behaviors"""
    
    def test_created_at_auto_now_add(self):
        """Test that created_at is automatically set on creation"""
        before_creation = timezone.now()
        job = self.create_sample_job()
        after_creation = timezone.now()
        
        self.assertGreaterEqual(job.created_at, before_creation)
        self.assertLessEqual(job.created_at, after_creation)
        self.assertIsInstance(job.created_at, datetime)
    
    def test_updated_at_auto_now(self):
        """Test that updated_at is automatically updated on save"""
        job = self.create_sample_job()
        original_updated = job.updated_at
        
        # Small delay to ensure timestamp difference
        import time
        time.sleep(0.01)
        
        job.title = 'Updated Title'
        job.save()
        
        self.assertGreater(job.updated_at, original_updated)
    
    def test_created_at_immutable(self):
        """Test that created_at doesn't change on updates"""
        job = self.create_sample_job()
        original_created = job.created_at
        
        # Update multiple times
        for i in range(3):
            job.title = f'Updated Title {i}'
            job.save()
            import time
            time.sleep(0.01)
        
        job.refresh_from_db()
        self.assertEqual(job.created_at, original_created)
    
    def test_timezone_aware_timestamps(self):
        """Test that timestamps are timezone-aware"""
        job = self.create_sample_job()
        
        self.assertIsNotNone(job.created_at.tzinfo)
        self.assertIsNotNone(job.updated_at.tzinfo)
        
        # Should use Django's timezone setting
        self.assertTrue(timezone.is_aware(job.created_at))
        self.assertTrue(timezone.is_aware(job.updated_at))


class JobDescriptionModelQuerySetTests( BaseSerializerTestCase):
    """Test QuerySet operations and database queries"""
    
    def test_filter_by_user(self):
        """Test filtering jobs by user"""
        job1 = self.create_sample_job(user=self.user1)
        job2 = self.create_sample_job(user=self.user2)
        job3 = self.create_sample_job(user=self.user1)
        
        user1_jobs = JobDescription.objects.filter(user=self.user1)
        user2_jobs = JobDescription.objects.filter(user=self.user2)
        
        self.assertEqual(user1_jobs.count(), 2)
        self.assertEqual(user2_jobs.count(), 1)
        
        self.assertIn(job1, user1_jobs)
        self.assertIn(job3, user1_jobs)
        self.assertIn(job2, user2_jobs)
    
    def test_filter_by_processed_status(self):
        """Test filtering by processing status"""
        processed_job = self.create_sample_job(is_processed=True)
        unprocessed_job = self.create_sample_job(is_processed=False)
        
        processed = JobDescription.objects.filter(is_processed=True)
        unprocessed = JobDescription.objects.filter(is_processed=False)
        
        self.assertIn(processed_job, processed)
        self.assertNotIn(unprocessed_job, processed)
        
        self.assertIn(unprocessed_job, unprocessed)
        self.assertNotIn(processed_job, unprocessed)
    
    def test_filter_by_active_status(self):
        """Test filtering by active status"""
        active_job = self.create_sample_job(is_active=True)
        inactive_job = self.create_sample_job(is_active=False)
        
        active_jobs = JobDescription.objects.filter(is_active=True)
        inactive_jobs = JobDescription.objects.filter(is_active=False)
        
        self.assertIn(active_job, active_jobs)
        self.assertNotIn(inactive_job, active_jobs)
        
        self.assertIn(inactive_job, inactive_jobs)
        self.assertNotIn(active_job, inactive_jobs)
    
    def test_filter_by_job_type(self):
        """Test filtering by job type"""
        full_time_job = self.create_sample_job(job_type='full_time')
        contract_job = self.create_sample_job(job_type='contract')
        remote_job = self.create_sample_job(job_type='remote')
        
        full_time_jobs = JobDescription.objects.filter(job_type='full_time')
        contract_jobs = JobDescription.objects.filter(job_type='contract')
        
        self.assertIn(full_time_job, full_time_jobs)
        self.assertNotIn(contract_job, full_time_jobs)
        self.assertNotIn(remote_job, full_time_jobs)
        
        self.assertIn(contract_job, contract_jobs)
        self.assertNotIn(full_time_job, contract_jobs)
    
    def test_complex_filtering(self):
        """Test complex filtering with multiple conditions"""
        # Create various jobs
        target_job = self.create_sample_job(
            user=self.user1,
            job_type='full_time',
            is_processed=True,
            is_active=True,
            company='Target Company'
        )
        
        
        self.create_sample_job(user=self.user2, job_type='full_time', is_processed=True),  # Different user
        self.create_sample_job(user=self.user1, job_type='contract', is_processed=True),  # Different type
        self.create_sample_job(user=self.user1, job_type='full_time', is_processed=False), # Not processed
        self.create_sample_job(user=self.user1, job_type='full_time', is_processed=True, is_active=False), # Not active
        
        
        # Complex filter
        results = JobDescription.objects.filter(
            user=self.user1,
            job_type='full_time',
            is_processed=True,
            is_active=True
        )
        
        self.assertEqual(results.count(), 1)
        self.assertEqual(results.first(), target_job)
    
    def test_ordering_queries(self):
        """Test ordering in queries"""
        import time
        job1 = self.create_sample_job(title='First Job')
        time.sleep(0.01)
        job2 = self.create_sample_job(title='Second Job')
        time.sleep(0.01)
        job3 = self.create_sample_job(title='Third Job')
        
        # Default ordering (by created_at desc)
        default_order = list(JobDescription.objects.all())
        self.assertEqual(default_order, [job3, job2, job1])
        
        # Order by title
        title_order = list(JobDescription.objects.order_by('title'))
        self.assertEqual(title_order, [job1, job2, job3])
        
        # Order by title desc
        title_desc_order = list(JobDescription.objects.order_by('-title'))
        self.assertEqual(title_desc_order, [job3, job2, job1])
    
    def test_aggregate_queries(self):
        """Test aggregate queries"""
        
        
        # Create test data
        self.create_sample_job(user=self.user1, is_processed=True)
        self.create_sample_job(user=self.user1, is_processed=False)
        self.create_sample_job(user=self.user2, is_processed=True)
        
        # Count by user
        user1_count = JobDescription.objects.filter(user=self.user1).count()
        user2_count = JobDescription.objects.filter(user=self.user2).count()
        
        self.assertEqual(user1_count, 2)
        self.assertEqual(user2_count, 1)
        
        # Count processed vs unprocessed
        processed_count = JobDescription.objects.filter(is_processed=True).count()
        unprocessed_count = JobDescription.objects.filter(is_processed=False).count()
        
        self.assertEqual(processed_count, 2)
        self.assertEqual(unprocessed_count, 1)
    
    def test_text_search_queries(self):
        """Test text-based search queries"""
        job1 = self.create_sample_job(
            title='Python Developer',
            company='Tech Corp',
            raw_content='Looking for Python developer with Django experience'
        )
        job2 = self.create_sample_job(
            title='Java Developer',
            company='Software Inc',
            raw_content='Java developer needed for enterprise applications'
        )
        job3 = self.create_sample_job(
            title='Data Scientist',
            company='AI Corp',
            raw_content='Data scientist role using Python and machine learning'
        )
        
        # Search in title
        python_title = JobDescription.objects.filter(title__icontains='python')
        self.assertIn(job1, python_title)
        self.assertNotIn(job2, python_title)
        
        # Search in company
        corp_company = JobDescription.objects.filter(company__icontains='corp')
        self.assertEqual(corp_company.count(), 2)
        self.assertIn(job1, corp_company)
        self.assertIn(job3, corp_company)
        
        # Search in raw_content
        python_content = JobDescription.objects.filter(raw_content__icontains='python')
        self.assertEqual(python_content.count(), 2)
        self.assertIn(job1, python_content)
        self.assertIn(job3, python_content)


class JobDescriptionModelEdgeCaseTests(BaseSerializerTestCase, TransactionTestCase):
    """Test edge cases and boundary conditions"""
    
    def test_unicode_content(self):
        """Test handling of unicode characters"""
        unicode_content = 'Développeur Python 🐍 at Société Générale'
        job = self.create_sample_job(
            title='Développeur Senior',
            company='Société Générale',
            raw_content=unicode_content,
            location='Paris, France 🇫🇷'
        )
        
        self.assertEqual(job.title, 'Développeur Senior')
        self.assertEqual(job.company, 'Société Générale')
        self.assertEqual(job.raw_content, unicode_content)
        self.assertEqual(job.location, 'Paris, France 🇫🇷')
    
    def test_very_long_content(self):
        """Test handling of very long content"""
        # Create very long content (1MB)
        very_long_content = 'A' * (1024 * 1024)
        
        job = self.create_sample_job(
            raw_content=very_long_content,
            requirements=very_long_content,
            skills_required=very_long_content
        )
        
        self.assertEqual(len(job.raw_content), 1024 * 1024)
        self.assertEqual(len(job.requirements), 1024 * 1024)
        self.assertEqual(len(job.skills_required), 1024 * 1024)
    
    def test_special_characters_in_fields(self):
        """Test handling of special characters"""
        special_chars = '!@#$%^&*()_+-=[]{}|;:,.<>?'
        
        job = self.create_sample_job(
            title=f'Special {special_chars} Job',
            company=f'Company {special_chars}',
            raw_content=f'Content with {special_chars} characters'
        )
        
        self.assertIn(special_chars, job.title)
        self.assertIn(special_chars, job.company)
        self.assertIn(special_chars, job.raw_content)
    
    def test_newlines_and_formatting(self):
        """Test handling of newlines and formatting characters"""
        formatted_content = """
        Job Title: Senior Developer
        
        Requirements:
        - 5+ years experience
        - Python/Django expertise
        
        Benefits:
        	• Health insurance
        	• Remote work
        	• Stock options
        """
        
        job = self.create_sample_job(raw_content=formatted_content)
        
        self.assertEqual(job.raw_content, formatted_content)
        self.assertIn('\n', job.raw_content)
        self.assertIn('\t', job.raw_content)
    
    def test_sql_injection_prevention(self):
        """Test that SQL injection attempts are handled safely"""
        malicious_content = "'; DROP TABLE jobs_jobdescription; --"
        
        job = self.create_sample_job(
            title=malicious_content,
            company=malicious_content,
            raw_content=malicious_content
        )
        
        # Should store the content as-is, not execute it
        self.assertEqual(job.title, malicious_content[:200])  # Truncated to max_length
        self.assertEqual(job.company, malicious_content[:200])
        self.assertEqual(job.raw_content, malicious_content)
        
        # Table should still exist
        self.assertTrue(JobDescription.objects.filter(id=job.id).exists())
    
    def test_extreme_timestamp_values(self):
        """Test behavior with extreme timestamp scenarios"""
        from datetime import timezone as dt_timezone
        past_date = timezone.datetime(2000, 1, 1, tzinfo=dt_timezone.utc)

        job = self.create_sample_job(created_at=past_date)  # Explicitly override
        
        self.assertEqual(job.created_at.year, 2000)

        # Update should still work with current timestamp
        job.title = 'Updated'
        job.save()

        self.assertGreater(job.updated_at, job.created_at)
    
    #COME BACK WHEN I USE POSTGRESQL DB
    # def test_concurrent_creation(self):
    #     import threading
    #     from django.db import connection
        
    #     results = []
    #     errors = []

    #     def create_job(user, title):
    #         try:
    #             # Ensure new DB connection in each thread
    #             connection.close()
    #             job = self.create_sample_job(user=user, title=title)
    #             results.append(job)
    #         except Exception as e:
    #             errors.append(e)
        
    #     threads = [
    #         threading.Thread(target=create_job, args=(self.user1, f'Concurrent Job {i}'))
    #         for i in range(5)
    #     ]
        
    #     for t in threads:
    #         t.start()
    #     for t in threads:
    #         t.join()
        
    #     self.assertEqual(len(results), 5)
    #     self.assertEqual(len(errors), 0)
    #     self.assertEqual(JobDescription.objects.count(), 5)

    
    def test_model_with_all_none_optional_fields(self):
        """Test model creation when all truly optional fields are None"""

        # ✅ Create a valid minimal job
        job = JobDescription.objects.create(
            user=self.user1,
            title="Untitled",  # required
            company="Untitled",
            location=None,
            salary_range=None,
            requirements=None,
            skills_required=None,
            experience_level=None,
            processing_notes=None
        )

        self.assertIsNotNone(job.id)
        self.assertEqual(job.job_type, 'unknown')  # default still applies

    
    def test_boundary_values_for_choice_fields(self):
        """Test boundary values for choice fields"""
        # Test with empty string (should work)
        job = self.create_sample_job(job_type='')
        self.assertEqual(job.job_type, '')
        
        # Test with very long choice value (should work at model level)
        job = self.create_sample_job(job_type='a' * 100)
        self.assertEqual(job.job_type, 'a' * 100)



        