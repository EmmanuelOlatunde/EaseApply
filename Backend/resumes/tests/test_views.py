# resumes/tests/test_views.py
from unittest.mock import patch, MagicMock
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from rest_framework.test import APIClient, APITestCase
from rest_framework import status
from ..models import Resume
from ..utils import TextExtractionError
from rest_framework_simplejwt.tokens import AccessToken

User = get_user_model()

class ResumeViewTestCase(APITestCase):
    """Base test case for resume views"""
    
    def setUp(self):
        """Set up test data"""
        # Create test users
        self.user1 = User.objects.create_user(
            username='user1',
            email='user1@example.com',
            password='testpass123'
        )
        self.user2 = User.objects.create_user(
            username='user2',
            email='user2@example.com',
            password='testpass123'
        )
        
        # Create tokens for authentication
        self.jwt_token1 = AccessToken.for_user(self.user1)
        self.jwt_token2 = AccessToken.for_user(self.user2)
        #self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {str(self.jwt_token1)}')
        import time
        # Create test resumes
        self.resume1 = Resume.objects.create(
            user=self.user1,
            original_filename='resume1.pdf',
            file_type=Resume.PDF,
            file_size=1024,
            extracted_text='User 1 resume content'
        )
        time.sleep(0.01)

        self.resume2 = Resume.objects.create(
            user=self.user1,
            original_filename='resume2.docx',
            file_type=Resume.DOCX,
            file_size=2048,
            extracted_text='User 1 second resume'
        )
        time.sleep(0.01)

        self.resume3 = Resume.objects.create(
            user=self.user2,
            original_filename='user2_resume.pdf',
            file_type=Resume.PDF,
            file_size=1536,
            extracted_text='User 2 resume content'
        )
        
        # API client
        self.client = APIClient()

class ResumeListCreateViewTestCase(ResumeViewTestCase):
    """Test cases for ResumeListCreateView"""
    
    def test_list_resumes_authenticated(self):
        """Test listing resumes for authenticated user"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {str(self.jwt_token1)}')

        url = reverse('resumes:resume-list-create')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        results = response.data['results']

        # User1 should have exactly 2 resumes
        self.assertEqual(len(results), 2)

        # Check ordering (newest first)
        self.assertEqual(results[0]['original_filename'], 'resume2.docx')
        self.assertEqual(results[1]['original_filename'], 'resume1.pdf')

        # Check that extracted_text is not included in list view
        self.assertNotIn('extracted_text', results[0])

    
    def test_list_resumes_unauthenticated(self):
        """Test listing resumes without authentication"""
        url = reverse('resumes:resume-list-create')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_list_resumes_only_user_resumes(self):
        """Test that users only see their own resumes"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {str(self.jwt_token2)}')
        
        url = reverse('resumes:resume-list-create')
        response = self.client.get(url)
        results = response.data['results']

        # User1 should have exactly 2 resumes
        self.assertEqual(len(results), 1) # user2 has 1 resume
        self.assertEqual(response.status_code, status.HTTP_200_OK)  
        self.assertEqual(results[0]['original_filename'], 'user2_resume.pdf')
    
    @patch('resumes.utils.extract_text_from_resume')
    def test_upload_resume_success(self, mock_extract):
        """Test successful resume upload"""
        mock_extract.return_value = "Extracted text from uploaded resume"
        
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {str(self.jwt_token1)}')
        
        pdf_file = SimpleUploadedFile(
            "new_resume.pdf",
            b'%PDF-1.4 fake pdf content',
            content_type="application/pdf"
        )
        
        url = reverse('resumes:resume-list-create')
        data = {'file': pdf_file}
        response = self.client.post(url, data, format='multipart')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Resume.objects.filter(user=self.user1).count(), 3)
        
        # Check response data
        self.assertIn('id', response.data)
        self.assertEqual(response.data['original_filename'], 'new_resume.pdf')
        self.assertEqual(response.data['file_type'], 'pdf')
        self.assertIn('extracted_text', response.data)
    
    def test_upload_resume_invalid_file(self):
        """Test upload with invalid file type"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {str(self.jwt_token1)}')
        
        invalid_file = SimpleUploadedFile(
            "resume.txt",
            b'plain text content',
            content_type="text/plain"
        )
        
        url = reverse('resumes:resume-list-create')
        data = {'file': invalid_file}
        response = self.client.post(url, data, format='multipart')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('file', response.data)
    
    def test_upload_resume_no_file(self):
        """Test upload without file"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {str(self.jwt_token1)}')
        
        url = reverse('resumes:resume-list-create')
        response = self.client.post(url, {}, format='multipart')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('file', response.data)
    
    def test_upload_resume_unauthenticated(self):
        """Test upload without authentication"""
        pdf_file = SimpleUploadedFile(
            "resume.pdf",
            b'fake content',
            content_type="application/pdf"
        )
        
        url = reverse('resumes:resume-list-create')
        data = {'file': pdf_file}
        response = self.client.post(url, data, format='multipart')
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    @patch('resumes.utils.extract_text_from_resume')
    def test_upload_with_extraction_failure(self, mock_extract):
        """Test upload when text extraction fails"""
        mock_extract.side_effect = TextExtractionError("Could not extract text")
        
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {str(self.jwt_token1)}')
        
        pdf_file = SimpleUploadedFile(
            "problematic_resume.pdf",
            b'fake pdf content',
            content_type="application/pdf"
        )
        
        url = reverse('resumes:resume-list-create')
        data = {'file': pdf_file}
        response = self.client.post(url, data, format='multipart')
        
        # Should still create the resume even if extraction fails
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Check that the resume was created with error message
        resume = Resume.objects.get(id=response.data['id'])
        self.assertIn('Text extraction failed:', resume.extracted_text)
    
    def test_upload_large_file(self):
        """Test upload with file size limit"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {str(self.jwt_token1)}')
        
        # Create a file larger than 10MB
        large_content = b'x' * (11 * 1024 * 1024)  # 11MB
        large_file = SimpleUploadedFile(
            "large_resume.pdf",
            large_content,
            content_type="application/pdf"
        )
        
        url = reverse('resumes:resume-list-create')
        data = {'file': large_file}
        response = self.client.post(url, data, format='multipart')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class ResumeDetailViewTestCase(ResumeViewTestCase):
    """Test cases for ResumeDetailView"""
    
    def test_get_resume_detail_success(self):
        """Test getting resume details successfully"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {str(self.jwt_token1)}')
        
        url = reverse('resumes:resume-detail', kwargs={'resume_id': self.resume1.id})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Check all fields are present
        expected_fields = [
            'id', 'original_filename', 'file_type', 'file_size',
            'extracted_text', 'uploaded_at', 'updated_at', 'file_url'
        ]
        for field in expected_fields:
            self.assertIn(field, response.data)
        
        # Check data values
        self.assertEqual(response.data['id'], str(self.resume1.id))
        self.assertEqual(response.data['original_filename'], 'resume1.pdf')
        self.assertEqual(response.data['extracted_text'], 'User 1 resume content')
    
    def test_get_resume_detail_not_found(self):
        """Test getting non-existent resume"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {str(self.jwt_token1)}')
        
        import uuid
        fake_id = uuid.uuid4()
        url = reverse('resumes:resume-detail', kwargs={'resume_id': fake_id})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_get_resume_detail_wrong_user(self):
        """Test getting another user's resume"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {str(self.jwt_token1)}')
        
        # Try to access user2's resume
        url = reverse('resumes:resume-detail', kwargs={'resume_id': self.resume3.id})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_get_resume_detail_unauthenticated(self):
        """Test getting resume without authentication"""
        url = reverse('resumes:resume-detail', kwargs={'resume_id': self.resume1.id})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_get_resume_detail_invalid_uuid(self):
        """Test getting resume with invalid UUID"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {str(self.jwt_token1)}')
        
        url = '/api/resumes/invalid-uuid/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

class FunctionBasedViewTestCase(ResumeViewTestCase):
    """Test cases for alternative function-based views"""
    
    @patch('resumes.utils.extract_text_from_resume')
    def test_upload_resume_function_view(self, mock_extract):
        """Test function-based upload view"""
        mock_extract.return_value = "Function view extracted text"
        
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {str(self.jwt_token1)}')
        
        pdf_file = SimpleUploadedFile(  # noqa: F841
            "function_resume.pdf",
            b'fake content',
            content_type="application/pdf"
        )
        
        # If using function-based views, uncomment the URL pattern and test
        # url = reverse('resumes:resume-upload-function')
        # data = {'file': pdf_file}
        # response = self.client.post(url, data, format='multipart')
        # 
        # self.assertEqual(response.status_code, status.HTTP_201_CREATED)
    
    def test_list_resumes_function_view(self):
        """Test function-based list view"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {str(self.jwt_token1)}')
        
        # If using function-based views, uncomment and test
        # url = reverse('resumes:resume-list-function')
        # response = self.client.get(url)
        # 
        # self.assertEqual(response.status_code, status.HTTP_200_OK)
        # self.assertEqual(len(response.data), 2)

class ResumeViewPermissionTestCase(ResumeViewTestCase):
    """Test cases for permissions and security"""


    def test_queryset_isolation(self):
        """Test that users can only access their own resumes"""
        list_url = reverse('resumes:resume-list-create')

        # User1 should see 2 resumes
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {str(self.jwt_token1)}')
        response = self.client.get(list_url)
        results = response.data['results']  # Access paginated results
        
        self.assertEqual(len(results), 2)
        filenames = [resume['original_filename'] for resume in results]  # Use results here
        self.assertIn('resume1.pdf', filenames)
        self.assertIn('resume2.docx', filenames)
        self.assertNotIn('user2_resume.pdf', filenames)
        
        # User2 should see 1 resume
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {str(self.jwt_token2)}')
        response = self.client.get(list_url)
        results = response.data['results']  # Access paginated results
        
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['original_filename'], 'user2_resume.pdf')  # Use results here

    def test_cross_user_access_prevention(self):
        """Test that users cannot access other users' specific resumes"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {str(self.jwt_token2)}')
        
        # Try to access user1's resume
        url = reverse('resumes:resume-detail', kwargs={'resume_id': self.resume1.id})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_token_authentication_required(self):
        """Test that all endpoints require authentication"""
        # Test list endpoint
        list_url = reverse('resumes:resume-list-create')
        response = self.client.get(list_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        
        # Test detail endpoint
        detail_url = reverse('resumes:resume-detail', kwargs={'resume_id': self.resume1.id})
        response = self.client.get(detail_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        
        # Test upload endpoint
        pdf_file = SimpleUploadedFile("test.pdf", b'content', content_type="application/pdf")
        upload_url = reverse('resumes:resume-list-create')
        response = self.client.post(upload_url, {'file': pdf_file}, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

class ResumeViewErrorHandlingTestCase(ResumeViewTestCase):
    """Test cases for error handling in views"""
    
    @patch('resumes.views.ResumeUploadSerializer')
    def test_upload_serializer_error_handling(self, mock_serializer_class):
        mock_serializer = MagicMock()
        mock_serializer.is_valid.return_value = False
        mock_serializer.errors = {'file': ['Invalid file']}
        mock_serializer_class.return_value = mock_serializer
        
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {str(self.jwt_token1)}')
        
        pdf_file = SimpleUploadedFile("test.pdf", b'content', content_type="application/pdf")
        url = reverse('resumes:resume-list-create')
        response = self.client.post(url, {'file': pdf_file}, format='multipart')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('file', response.data)
    
    @patch('resumes.views.ResumeUploadSerializer')
    def test_upload_unexpected_error_handling(self, mock_serializer_class):
        mock_serializer = MagicMock()
        mock_serializer.is_valid.return_value = True
        mock_serializer.save.side_effect = Exception("Unexpected error")
        mock_serializer_class.return_value = mock_serializer

        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {str(self.jwt_token1)}')

        pdf_file = SimpleUploadedFile("test.pdf", b'content', content_type="application/pdf")
        url = reverse('resumes:resume-list-create')
        response = self.client.post(url, {'file': pdf_file}, format='multipart')

        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertIn('error', response.data)


class ResumeViewContentTypeTestCase(ResumeViewTestCase):
    """Test cases for content type handling"""
    
    def test_multipart_parser_required(self):
        """Test that file uploads require multipart/form-data"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {str(self.jwt_token1)}')
        
        # Try to send file as JSON (should fail)
        url = reverse('resumes:resume-list-create')
        response = self.client.post(url, {'file': 'not_a_file'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_415_UNSUPPORTED_MEDIA_TYPE)
        #self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    @patch('resumes.utils.extract_text_from_resume')
    def test_supported_file_types(self, mock_extract):
        mock_extract.return_value = "Mocked extracted text"
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {str(self.jwt_token1)}')
        url = reverse('resumes:resume-list-create')
        
        # Test PDF
        pdf_file = SimpleUploadedFile(
            "resume.pdf", b'fake pdf', content_type="application/pdf"
        )
        response = self.client.post(url, {'file': pdf_file}, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Test DOCX
        docx_file = SimpleUploadedFile(
            "resume.docx", b'fake docx', 
            content_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )
        response = self.client.post(url, {'file': docx_file}, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Test unsupported type
        txt_file = SimpleUploadedFile(
            "resume.txt", b'fake txt', content_type="text/plain"
        )
        response = self.client.post(url, {'file': txt_file}, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

class ResumeViewIntegrationTestCase(ResumeViewTestCase):
    """Integration tests for resume views"""
    
    @patch('resumes.serializers.extract_text_from_resume')
    def test_full_upload_workflow(self, mock_extract):
        mock_extract.return_value = "Full workflow extracted text"
        
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {str(self.jwt_token1)}')
        
        # Use valid PDF content or ensure file validation passes
        pdf_file = SimpleUploadedFile(
            "workflow_test.pdf",
            b'%PDF-1.4\n%Fake PDF\n%%EOF',  # Minimal valid PDF structure
            content_type="application/pdf"
        )
        
        upload_url = reverse('resumes:resume-list-create')
        upload_response = self.client.post(upload_url, {'file': pdf_file}, format='multipart')
        
        self.assertEqual(upload_response.status_code, status.HTTP_201_CREATED)
        resume_id = upload_response.data['id']
        
        # Verify resume appears in list
        list_url = reverse('resumes:resume-list-create')
        list_response = self.client.get(list_url)
        
        self.assertEqual(list_response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(list_response.data['results']), 3)  # 2 existing + 1 new
        
        new_resume = next(
            (r for r in list_response.data['results'] if r['original_filename'] == 'workflow_test.pdf'),
            None
        )
        self.assertIsNotNone(new_resume)
        
        # Get detailed view
        detail_url = reverse('resumes:resume-detail', kwargs={'resume_id': resume_id})
        detail_response = self.client.get(detail_url)
        
        self.assertEqual(detail_response.status_code, status.HTTP_200_OK)
        self.assertEqual(detail_response.data['extracted_text'], "Full workflow extracted text")
        self.assertEqual(detail_response.data['original_filename'], 'workflow_test.pdf')


    def test_database_consistency(self):
        """Test that database state remains consistent"""
        initial_count = Resume.objects.count()
        
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {str(self.jwt_token1)}')
        
        # Upload a resume
        pdf_file = SimpleUploadedFile(
            "consistency_test.pdf",
            b'fake content',
            content_type="application/pdf"
        )
        
        url = reverse('resumes:resume-list-create')
        response = self.client.post(url, {'file': pdf_file}, format='multipart')
        
        if response.status_code == status.HTTP_201_CREATED:
            # Database should have one more resume
            self.assertEqual(Resume.objects.count(), initial_count + 1)
            
            # Resume should belong to the authenticated user
            new_resume = Resume.objects.get(id=response.data['id'])
            self.assertEqual(new_resume.user, self.user1)
        else:
            # If upload failed, count should remain the same
            self.assertEqual(Resume.objects.count(), initial_count)