# resumes/tests/test_serializers.py
from unittest.mock import patch
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APIRequestFactory
from rest_framework.request import Request
from ..models import Resume
from ..serializers import (
    ResumeUploadSerializer, 
    ResumeListSerializer, 
    ResumeDetailSerializer
)
from ..utils import TextExtractionError

User = get_user_model()

class ResumeSerializerTestCase(TestCase):
    """Base test case for resume serializers"""
    
    def setUp(self):
        """Set up test data"""
        import time
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        # Create mock request
        self.factory = APIRequestFactory()
        request = self.factory.get('/')

        request.user = self.user 
        self.request = Request(request)
        # Create test resume
        self.resume = Resume.objects.create(
            user=self.user,
            original_filename='test_resume.pdf',
            file_type=Resume.PDF,
            file_size=1024,
            extracted_text='Test extracted content from PDF'
        )
        time.sleep(0.01)
        

class ResumeUploadSerializerTestCase(ResumeSerializerTestCase):
    """Test cases for ResumeUploadSerializer"""
    
    def test_valid_pdf_upload(self):
        """Test valid PDF file upload"""
        pdf_content = b'%PDF-1.4 fake pdf content'
        pdf_file = SimpleUploadedFile(
            "resume.pdf",
            pdf_content,
            content_type="application/pdf"
        )
        
        data = {'file': pdf_file}
        serializer = ResumeUploadSerializer(
            data=data,
            context={'request': self.request}
        )
        
        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.context['file_type'], 'pdf')
    
    def test_valid_docx_upload(self):
        """Test valid DOCX file upload"""
        docx_content = b'fake docx content'
        docx_file = SimpleUploadedFile(
            "resume.docx",
            docx_content,
            content_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )
        
        data = {'file': docx_file}
        serializer = ResumeUploadSerializer(
            data=data,
            context={'request': self.request}
        )
        
        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.context['file_type'], 'docx')
    
    def test_invalid_file_type(self):
        """Test invalid file type upload"""
        invalid_file = SimpleUploadedFile(
            "resume.txt",
            b"fake txt content",
            content_type="text/plain"
        )
        
        data = {'file': invalid_file}
        serializer = ResumeUploadSerializer(
            data=data,
            context={'request': self.request}
        )
        
        self.assertFalse(serializer.is_valid())
        self.assertIn('file', serializer.errors)
        self.assertIn('Invalid file', str(serializer.errors['file'][0]))
    
    def test_file_too_large(self):
        """Test file size validation"""
        # Create a file larger than 10MB
        large_content = b'x' * (11 * 1024 * 1024)  # 11MB
        large_file = SimpleUploadedFile(
            "resume.pdf",
            large_content,
            content_type="application/pdf"
        )
        
        data = {'file': large_file}
        serializer = ResumeUploadSerializer(
            data=data,
            context={'request': self.request}
        )
        
        self.assertFalse(serializer.is_valid())
        self.assertIn('file', serializer.errors)
    
    def test_no_file_provided(self):
        """Test missing file in upload"""
        data = {}
        serializer = ResumeUploadSerializer(
            data=data,
            context={'request': self.request}
        )
        
        self.assertFalse(serializer.is_valid())
        self.assertIn('file', serializer.errors)
    
    @patch('resumes.serializers.extract_text_from_resume')
    def test_successful_text_extraction(self, mock_extract):
        """Test successful text extraction during creation"""
        mock_extract.return_value = "Extracted text from resume"
        
        pdf_file = SimpleUploadedFile(
            "resume.pdf",
            b'%PDF-1.4 fake pdf content',
            content_type="application/pdf"
        )
        
        data = {'file': pdf_file}
        request = self.factory.post("/")
        request.user = self.user

        serializer = ResumeUploadSerializer(
            data=data,
            context={"request": request, "file_type": "PDF"}
        )
        
        self.assertTrue(serializer.is_valid())
        resume = serializer.save()
        
        self.assertEqual(resume.user, self.user)
        self.assertEqual(resume.extracted_text, "Extracted text from resume")
        self.assertEqual(resume.file_type, 'pdf')
        self.assertEqual(resume.original_filename, 'resume.pdf')
        
        mock_extract.assert_called_once()
    
    @patch('resumes.serializers.extract_text_from_resume')
    def test_text_extraction_failure(self, mock_extract):
        """Test handling of text extraction failure"""
        mock_extract.side_effect = TextExtractionError("Could not extract text")
        
        pdf_file = SimpleUploadedFile(
            "resume.pdf",
            b'%PDF-1.4 fake pdf content',
            content_type="application/pdf"
        )
        
        data = {'file': pdf_file}
        request = self.factory.post("/")
        request.user = self.user

        serializer = ResumeUploadSerializer(
            data=data,
            context={"request": request, "file_type": "PDF"}
        )
        
        self.assertTrue(serializer.is_valid())
        resume = serializer.save()
        
        self.assertEqual(resume.user, self.user)
        self.assertIn("Text extraction failed:", resume.extracted_text)
        self.assertIn("Could not extract text", resume.extracted_text)
    
    @patch('resumes.serializers.extract_text_from_resume')
    def test_unexpected_extraction_error(self, mock_extract):
        """Test handling of unexpected errors during extraction"""
        mock_extract.side_effect = Exception("Unexpected error")
        
        pdf_file = SimpleUploadedFile(
            "resume.pdf",
            b'%PDF-1.4 fake pdf content',
            content_type="application/pdf"
        )
        
        data = {'file': pdf_file}

        request = self.factory.post("/")
        request.user = self.user

        serializer = ResumeUploadSerializer(
            data=data,
            context={"request": request, "file_type": "PDF"}
        )

        
        self.assertTrue(serializer.is_valid())
        resume = serializer.save()
        
        self.assertEqual(resume.extracted_text, 
                        "Text extraction failed due to an unexpected error.")
    
    def test_serializer_fields(self):
        """Test serializer fields configuration"""
        serializer = ResumeUploadSerializer()
        
        # Check field configuration
        self.assertIn('file', serializer.fields)
        self.assertIn('extracted_text', serializer.fields)
        self.assertIn('id', serializer.fields)
        
        # Check read-only fields
        self.assertTrue(serializer.fields['extracted_text'].read_only)
        self.assertTrue(serializer.fields['id'].read_only)
        
        # Check write-only fields
        self.assertTrue(serializer.fields['file'].write_only)

class ResumeListSerializerTestCase(ResumeSerializerTestCase):
    """Test cases for ResumeListSerializer"""
    
    def test_serialization(self):
        """Test resume list serialization"""
        serializer = ResumeListSerializer(
            self.resume,
            context={'request': self.request}
        )
        
        data = serializer.data
        
        # Check included fields
        expected_fields = [
            'id', 'original_filename', 'file_type', 
            'file_size', 'uploaded_at', 'updated_at'
        ]
        
        for field in expected_fields:
            self.assertIn(field, data)
        
        # Check excluded fields (should not include extracted_text)
        self.assertNotIn('extracted_text', data)
        
        # Check data values
        self.assertEqual(data['original_filename'], 'test_resume.pdf')
        self.assertEqual(data['file_type'], 'pdf')
        self.assertEqual(data['file_size'], 1024)
    
    def test_multiple_resumes_serialization(self):
        """Test serializing multiple resumes"""
        # Create additional resume
        resume2 = Resume.objects.create(  # noqa: F841
            user=self.user,
            original_filename='resume2.docx',
            file_type=Resume.DOCX,
            file_size=2048,
            extracted_text='Another resume content'
        )
        
        resumes = Resume.objects.filter(user=self.user)
        serializer = ResumeListSerializer(
            resumes,
            many=True,
            context={'request': self.request}
        )
        
        data = serializer.data
        
        self.assertEqual(len(data), 2)
        
        # Check ordering (newest first)
        self.assertEqual(data[0]['original_filename'], 'resume2.docx')
        self.assertEqual(data[1]['original_filename'], 'test_resume.pdf')

class ResumeDetailSerializerTestCase(ResumeSerializerTestCase):
    """Test cases for ResumeDetailSerializer"""
    
    def test_serialization_with_extracted_text(self):
        """Test detailed resume serialization including extracted text"""
        serializer = ResumeDetailSerializer(
            self.resume,
            context={'request': self.request}
        )
        
        data = serializer.data
        
        # Check all fields are included
        expected_fields = [
            'id', 'original_filename', 'file_type', 'file_size',
            'extracted_text', 'uploaded_at', 'updated_at', 'file_url'
        ]
        
        for field in expected_fields:
            self.assertIn(field, data)
        
        # Check extracted text is included
        self.assertEqual(data['extracted_text'], 'Test extracted content from PDF')
        
        # Check other data
        self.assertEqual(data['original_filename'], 'test_resume.pdf')
        self.assertEqual(data['file_type'], 'pdf')
        self.assertEqual(data['file_size'], 1024)
    
    def test_file_url_generation(self):
        """Test file URL generation"""
        # Create resume with actual file
        pdf_file = SimpleUploadedFile(
            "test.pdf",
            b'fake content',
            content_type="application/pdf"
        )
        
        resume_with_file = Resume.objects.create(
            user=self.user,
            file=pdf_file,
            original_filename='test.pdf',
            file_type=Resume.PDF,
            file_size=1024
        )
        
        serializer = ResumeDetailSerializer(
            resume_with_file,
            context={'request': self.request}
        )
        
        data = serializer.data
        
        # Should have file_url
        self.assertIn('file_url', data)
        self.assertIsNotNone(data['file_url'])
        self.assertIn('http', data['file_url'])
    
    def test_no_file_url_when_no_file(self):
        """Test file URL when no file is attached"""
        resume_no_file = Resume.objects.create(
            user=self.user,
            original_filename='test.pdf',
            file_type=Resume.PDF,
            file_size=1024
        )
        
        serializer = ResumeDetailSerializer(
            resume_no_file,
            context={'request': self.request}
        )
        
        data = serializer.data
        
        # Should have file_url but it should be None
        self.assertIn('file_url', data)
        self.assertIsNone(data['file_url'])
    
    def test_serialization_without_request_context(self):
        """Test serialization when request context is missing"""
        serializer = ResumeDetailSerializer(self.resume)
        
        data = serializer.data
        
        # Should still work but file_url should be None
        self.assertIn('file_url', data)
        self.assertIsNone(data['file_url'])

class SerializerValidationTestCase(ResumeSerializerTestCase):
    """Additional validation tests for serializers"""
    
    def test_upload_serializer_context_requirement(self):
        """Test that upload serializer requires request context"""
        pdf_file = SimpleUploadedFile(
            "resume.pdf",
            b'fake content',
            content_type="application/pdf"
        )
        
        data = {'file': pdf_file}
        
        # Without context, should still validate the file
        serializer = ResumeUploadSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        
        # But save should fail without request context
        with self.assertRaises(AttributeError):
            serializer.save()
    
    def test_serializer_meta_configuration(self):
        """Test serializer Meta class configurations"""
        # ResumeUploadSerializer
        upload_meta = ResumeUploadSerializer.Meta
        self.assertEqual(upload_meta.model, Resume)
        self.assertIn('file', upload_meta.fields)
        self.assertIn('extracted_text', upload_meta.read_only_fields)
        
        # ResumeListSerializer
        list_meta = ResumeListSerializer.Meta
        self.assertEqual(list_meta.model, Resume)
        self.assertNotIn('extracted_text', list_meta.fields)
        
        # ResumeDetailSerializer
        detail_meta = ResumeDetailSerializer.Meta
        self.assertEqual(detail_meta.model, Resume)
        self.assertIn('extracted_text', detail_meta.fields)
        self.assertIn('file_url', detail_meta.fields)
        
    @patch('resumes.serializers.validate_resume_file')
    def test_file_validation_called(self, mock_validate):
        """Test that file validation utility is called"""
        mock_validate.return_value = ('pdf', True)
        
        pdf_file = SimpleUploadedFile(
            "resume.pdf",
            b'fake content',
            content_type="application/pdf"
        )
        
        data = {'file': pdf_file}
        serializer = ResumeUploadSerializer(
            data=data,
            context={'request': self.request}
        )
        
        serializer.is_valid(raise_exception=True)
        
        mock_validate.assert_called_once_with(pdf_file)
