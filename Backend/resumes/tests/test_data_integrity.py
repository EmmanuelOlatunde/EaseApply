"""
Data integrity tests for the resume application
"""
from django.test import TestCase, TransactionTestCase
from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from django.core.exceptions import ValidationError
from ..models import Resume

User = get_user_model()


class ResumeDataIntegrityTestCase(TestCase):
    """Test data integrity constraints and validation"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='integrityuser',
            email='integrity@example.com',
            password='testpass123'
        )
    
    def test_required_fields_validation(self):
        """Test that required fields are properly validated"""
        # Try to create resume without required fields
        with self.assertRaises(IntegrityError):
            Resume.objects.create()  # No user specified
    
    def test_user_foreign_key_constraint(self):
        """Test foreign key constraint for user field"""
        resume = Resume(
            user=self.user,
            original_filename='test.pdf',
            file_type=Resume.PDF,
            file_size=1024
        )
        resume.save()
        
        # Resume should be linked to user
        self.assertEqual(resume.user, self.user)
        self.assertIn(resume, self.user.resumes.all())
    
    def test_file_type_choices_validation(self):
        """Test file type choices are enforced"""
        resume = Resume.objects.create(
            user=self.user,
            original_filename='test.pdf',
            file_type='invalid_type',  # Invalid choice
            file_size=1024
        )
        
        # Should save but may cause issues in forms/serializers
        self.assertEqual(resume.file_type, 'invalid_type')
        
        # Full clean should catch this
        with self.assertRaises(ValidationError):
            resume.full_clean()
    
    def test_json_field_integrity(self):
        """Test JSON field data integrity"""
        resume = Resume.objects.create(
            user=self.user,
            original_filename='test.pdf',
            file_type=Resume.PDF,
            file_size=1024
        )
        
        # Test valid JSON data
        resume.contact_info = {'email': 'test@example.com', 'phone': '123-456-7890'}
        resume.skills = ['Python', 'Django', 'JavaScript']
        resume.work_experience = [{
            'title': 'Developer',
            'company': 'Tech Corp',
            'duration': '2020-2023'
        }]
        resume.save()
        
        # Refresh from database
        resume.refresh_from_db()
        
        self.assertEqual(resume.contact_info['email'], 'test@example.com')
        self.assertEqual(len(resume.skills), 3)
        self.assertEqual(resume.work_experience[0]['title'], 'Developer')
    
    def test_uuid_uniqueness(self):
        """Test that UUID primary keys are unique"""
        resume1 = Resume.objects.create(
            user=self.user,
            original_filename='test1.pdf',
            file_type=Resume.PDF,
            file_size=1024
        )
        
        resume2 = Resume.objects.create(
            user=self.user,
            original_filename='test2.pdf',
            file_type=Resume.PDF,
            file_size=1024
        )
        
        # UUIDs should be different
        self.assertNotEqual(resume1.id, resume2.id)
    
    def test_file_size_validation(self):
        """Test file size field validation"""
        # Test with valid file size
        resume = Resume.objects.create(
            user=self.user,
            original_filename='test.pdf',
            file_type=Resume.PDF,
            file_size=1024
        )
        self.assertEqual(resume.file_size, 1024)
        
        # Test with zero file size
        resume_zero = Resume.objects.create(
            user=self.user,
            original_filename='empty.pdf',
            file_type=Resume.PDF,
            file_size=0
        )
        self.assertEqual(resume_zero.file_size, 0)
        
        # Test with negative file size (should be prevented by PositiveIntegerField)
        with self.assertRaises(IntegrityError):
            Resume.objects.create(
                user=self.user,
                original_filename='negative.pdf',
                file_type=Resume.PDF,
                file_size=-1
            )
    
    def test_timestamp_integrity(self):
        """Test timestamp field integrity"""
        import time
        from django.utils import timezone
        
        before_creation = timezone.now()
        time.sleep(0.01)  # Small delay
        
        resume = Resume.objects.create(
            user=self.user,
            original_filename='timestamp_test.pdf',
            file_type=Resume.PDF,
            file_size=1024
        )
        
        time.sleep(0.01)
        after_creation = timezone.now()
        
        # uploaded_at should be set automatically
        self.assertIsNotNone(resume.uploaded_at)
        self.assertGreater(resume.uploaded_at, before_creation)
        self.assertLess(resume.uploaded_at, after_creation)
        
        # updated_at should be set automatically
        self.assertIsNotNone(resume.updated_at) 
        
        # Update the resume
        original_updated_at = resume.updated_at
        time.sleep(0.01)
        resume.extracted_text = 'Updated content'
        resume.save()
        
        # updated_at should change
        self.assertGreater(resume.updated_at, original_updated_at)
    
    def test_cascade_deletion_integrity(self):
        """Test that cascade deletion works properly"""
        resume = Resume.objects.create(
            user=self.user,
            original_filename='cascade_test.pdf',
            file_type=Resume.PDF,
            file_size=1024
        )
        
        resume_id = resume.id
        user_id = self.user.id
        
        # Delete user should cascade delete resume
        self.user.delete()
        
        # Resume should be deleted
        self.assertFalse(Resume.objects.filter(id=resume_id).exists())
        self.assertFalse(User.objects.filter(id=user_id).exists())


class ResumeTransactionIntegrityTestCase(TransactionTestCase):
    """Test transaction integrity for resume operations"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='transuser',
            email='trans@example.com',
            password='testpass123'
        )
    
    def test_atomic_resume_creation(self):
        """Test that resume creation is atomic"""
        from unittest.mock import patch
        
        # Mock a failure during save to test atomicity
        with patch.object(Resume, 'save', side_effect=Exception("Simulated failure")):
            with self.assertRaises(Exception):
                with transaction.atomic():
                    resume = Resume(
                        user=self.user,
                        original_filename='atomic_test.pdf',
                        file_type=Resume.PDF,
                        file_size=1024
                    )
                    resume.save()
        
        # No partial data should be saved
        self.assertEqual(Resume.objects.filter(original_filename='atomic_test.pdf').count(), 0)
    
    def test_concurrent_resume_modification(self):
        """Test handling of concurrent modifications"""
        resume = Resume.objects.create(
            user=self.user,
            original_filename='concurrent_test.pdf',
            file_type=Resume.PDF,
            file_size=1024,
            extracted_text="Original content"
        )
        
        # Simulate concurrent modification
        resume1 = Resume.objects.get(id=resume.id)
        resume2 = Resume.objects.get(id=resume.id)
        
        # Modify both instances
        resume1.extracted_text = "Modified by process 1"
        resume2.extracted_text = "Modified by process 2"
        
        # Save both (last one wins)
        resume1.save()
        resume2.save()
        
        # Verify final state
        final_resume = Resume.objects.get(id=resume.id)
        self.assertEqual(final_resume.extracted_text, "Modified by process 2")

