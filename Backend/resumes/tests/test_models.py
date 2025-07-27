# resumes/tests/test_models.py
import os
import uuid
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from ..models import Resume, resume_upload_path

User = get_user_model()

class ResumeModelTestCase(TestCase):
    """Test cases for Resume model"""
    
    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.user2 = User.objects.create_user(
            username='testuser2',
            email='test2@example.com',
            password='testpass123'
        )
    
    def test_resume_creation(self):
        """Test basic resume creation"""
        resume = Resume.objects.create(
            user=self.user,
            original_filename='test_resume.pdf',
            file_type=Resume.PDF,
            file_size=1024,
            extracted_text='Test content'
        )
        
        self.assertEqual(resume.user, self.user)
        self.assertEqual(resume.original_filename, 'test_resume.pdf')
        self.assertEqual(resume.file_type, Resume.PDF)
        self.assertEqual(resume.file_size, 1024)
        self.assertEqual(resume.extracted_text, 'Test content')
        self.assertIsInstance(resume.id, uuid.UUID)
        self.assertIsNotNone(resume.uploaded_at)
        self.assertIsNotNone(resume.updated_at)
    
    def test_resume_str_representation(self):
        """Test string representation of Resume"""
        resume = Resume.objects.create(
            user=self.user,
            original_filename='my_resume.pdf',
            file_type=Resume.PDF,
            file_size=2048
        )
        
        expected_str = f"{self.user.username} - my_resume.pdf"
        self.assertEqual(str(resume), expected_str)
    
    def test_resume_ordering(self):
        import time
        """Test that resumes are ordered by upload date (newest first)"""
        resume1 = Resume.objects.create(
            user=self.user,
            original_filename='resume1.pdf',
            file_type=Resume.PDF,
            file_size=1024
        )
        time.sleep(0.01)
        resume2 = Resume.objects.create(
            user=self.user,
            original_filename='resume2.pdf',
            file_type=Resume.PDF,
            file_size=1024
        )
        
        resumes = list(Resume.objects.all())
        self.assertEqual(resumes[0], resume2)  # Newest first
        self.assertEqual(resumes[1], resume1)
    
    def test_user_relationship(self):
        """Test user foreign key relationship"""
        resume = Resume.objects.create(
            user=self.user,
            original_filename='test.pdf',
            file_type=Resume.PDF,
            file_size=1024
        )
        
        # Test forward relationship
        self.assertEqual(resume.user, self.user)
        
        # Test reverse relationship
        self.assertIn(resume, self.user.resumes.all())
        self.assertEqual(self.user.resumes.count(), 1)
    
    def test_cascade_delete(self):
        """Test that resumes are deleted when user is deleted"""
        resume = Resume.objects.create(
            user=self.user,
            original_filename='test.pdf',
            file_type=Resume.PDF,
            file_size=1024
        )
        
        self.assertEqual(Resume.objects.count(), 1)
        
        # Delete user should cascade delete resume
        self.user.delete()
        self.assertEqual(Resume.objects.count(), 0)
    
    def test_file_type_choices(self):
        """Test file type choices validation"""
        # Valid file types
        pdf_resume = Resume.objects.create(
            user=self.user,
            original_filename='test.pdf',
            file_type=Resume.PDF,
            file_size=1024
        )
        self.assertEqual(pdf_resume.file_type, Resume.PDF)
        
        docx_resume = Resume.objects.create(
            user=self.user,
            original_filename='test.docx',
            file_type=Resume.DOCX,
            file_size=1024
        )
        self.assertEqual(docx_resume.file_type, Resume.DOCX)
    
    def test_file_extension_validator(self):
        """Test file extension validation"""
        # Create mock files with different extensions
        valid_pdf = SimpleUploadedFile(
            "test.pdf", b"fake pdf content", content_type="application/pdf"
        )
        valid_docx = SimpleUploadedFile(
            "test.docx", b"fake docx content", 
            content_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )
        
        # These should work
        resume1 = Resume(
            user=self.user,
            file=valid_pdf,
            original_filename='test.pdf',
            file_type=Resume.PDF,
            file_size=1024
        )
        resume1.full_clean()  # Should not raise
        
        resume2 = Resume(
            user=self.user,
            file=valid_docx,
            original_filename='test.docx',
            file_type=Resume.DOCX,
            file_size=1024
        )
        resume2.full_clean()  # Should not raise
    
    def test_auto_file_type_detection_on_save(self):
        """Test automatic file type detection on save"""
        # PDF file
        pdf_file = SimpleUploadedFile(
            "resume.pdf", b"fake pdf content", content_type="application/pdf"
        )
        resume_pdf = Resume(
            user=self.user,
            file=pdf_file,
            file_size=1024
        )
        resume_pdf.save()
        
        self.assertEqual(resume_pdf.file_type, Resume.PDF)
        self.assertEqual(resume_pdf.original_filename, 'resume.pdf')
        
        # DOCX file
        docx_file = SimpleUploadedFile(
            "resume.docx", b"fake docx content"
        )
        resume_docx = Resume(
            user=self.user2,
            file=docx_file,
            file_size=2048
        )
        resume_docx.save()
        
        self.assertEqual(resume_docx.file_type, Resume.DOCX)
        self.assertEqual(resume_docx.original_filename, 'resume.docx')
    
    def test_file_size_auto_detection(self):
        """Test automatic file size detection on save"""
        file_content = b"fake content" * 100  # 1200 bytes
        test_file = SimpleUploadedFile(
            "test.pdf", file_content, content_type="application/pdf"
        )
        
        resume = Resume(
            user=self.user,
            file=test_file
        )
        resume.save()
        
        self.assertEqual(resume.file_size, len(file_content))
    
    def test_blank_extracted_text(self):
        """Test that extracted_text can be blank"""
        resume = Resume.objects.create(
            user=self.user,
            original_filename='test.pdf',
            file_type=Resume.PDF,
            file_size=1024,
            extracted_text=None
        )
        
        self.assertIsNone(resume.extracted_text)
        
        # Test empty string
        resume.extracted_text = ""
        resume.save()
        self.assertEqual(resume.extracted_text, "")
    
    def test_multiple_resumes_per_user(self):
        """Test that a user can have multiple resumes"""
        resume1 = Resume.objects.create(
            user=self.user,
            original_filename='resume1.pdf',
            file_type=Resume.PDF,
            file_size=1024
        )
        resume2 = Resume.objects.create(
            user=self.user,
            original_filename='resume2.docx',
            file_type=Resume.DOCX,
            file_size=2048
        )
        
        self.assertEqual(self.user.resumes.count(), 2)
        self.assertIn(resume1, self.user.resumes.all())
        self.assertIn(resume2, self.user.resumes.all())
    
    
    def test_resume_upload_path_function(self):
        """Test the resume upload path function"""
        resume = Resume(
            user=self.user,
            original_filename='test.pdf',
            file_type=Resume.PDF,
            file_size=1024
        )
        
        path = resume_upload_path(resume, 'original_filename.pdf')
        
        # Convert path to use forward slashes for consistent checks
        normalized_path = path.replace('\\', '/')
        
        # Should contain user ID and be in resumes directory
        self.assertIn(f'resumes/{str(self.user.id)}/', normalized_path)
        self.assertTrue(normalized_path.endswith('.pdf'))
        
        # Should use UUID for filename
        filename = os.path.basename(path)
        filename_without_ext = filename.split('.')[0]
        
        # Check if it's a valid UUID format
        try:
            uuid.UUID(filename_without_ext)
        except ValueError:
            self.fail("Generated filename is not a valid UUID") 
    
    
    
    def test_database_indexes(self):
        """Test that database indexes are properly created"""
        # This is more of a smoke test - actual index testing would require 
        # database introspection which varies by database backend
        
        # Create some test data
        for i in range(5):
            Resume.objects.create(
                user=self.user,
                original_filename=f'resume_{i}.pdf',
                file_type=Resume.PDF,
                file_size=1024 * i
            )
        
        # Query that should use the index
        resumes = Resume.objects.filter(user=self.user).order_by('-uploaded_at')
        self.assertEqual(resumes.count(), 5)
    
    def test_model_fields_max_lengths(self):
        """Test model field constraints"""
        # Test original_filename max length
        long_filename = 'a' * 300  # Longer than 255 chars
        
        resume = Resume(
            user=self.user,
            original_filename=long_filename,
            file_type=Resume.PDF,
            file_size=1024
        )
        
        with self.assertRaises(ValidationError):
            resume.full_clean()
    
    def test_model_meta_options(self):
        """Test model Meta options"""
        self.assertEqual(Resume._meta.ordering, ['-uploaded_at'])
        
        # Check if indexes are defined
        index_fields = []
        for index in Resume._meta.indexes:
            index_fields.extend(index.fields)
        
        self.assertIn('user', index_fields)
        self.assertIn('-uploaded_at', index_fields)