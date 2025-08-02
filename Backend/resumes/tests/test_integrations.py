"""
Integration tests for the resume application
Tests the complete workflow from upload to parsing
"""
from unittest.mock import patch
from django.test import TransactionTestCase
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from rest_framework_simplejwt.tokens import AccessToken
from ..models import Resume
from ..utils import TextExtractionError

User = get_user_model()


class ResumeWorkflowIntegrationTestCase(APITestCase):
    """Test complete resume workflow integration"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='integrationuser',
            email='integration@example.com',
            password='testpass123'
        )
        self.jwt_token = AccessToken.for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {str(self.jwt_token)}')
    
    @patch('resumes.serializers.extract_text_from_resume')
    @patch('resumes.serializers.parse_resume_content')
    def test_complete_pdf_upload_and_parsing_workflow(self, mock_parse, mock_extract):
        """Test complete workflow from PDF upload to parsing"""
        # Mock text extraction
        mock_extract.return_value = """
        John Doe
        Software Engineer
        Email: john.doe@example.com
        Phone: (555) 123-4567
        
        SUMMARY
        Experienced software engineer with 5 years of experience
        
        SKILLS
        Python, Django, JavaScript, React
        
        EXPERIENCE
        Senior Developer | Tech Corp | 2020-2023
        • Developed web applications
        • Led team of 3 developers
        
        EDUCATION
        BS Computer Science | University of Tech | 2018
        """
        
        # Mock parsing
        mock_parse.return_value = {
            'fullName': 'John Doe',
            'summary': 'Experienced software engineer with 5 years of experience',
            'contactInfo': {
                'email': 'john.doe@example.com',
                'phone': '(555) 123-4567'
            },
            'skills': ['Python', 'Django', 'JavaScript', 'React'],
            'workExperience': [{
                'title': 'Senior Developer',
                'company': 'Tech Corp',
                'duration': '2020-2023',
                'description': ['Developed web applications', 'Led team of 3 developers']
            }],
            'education': [{
                'degree': 'BS Computer Science',
                'institution': 'University of Tech',
                'year': '2018'
            }],
            'certifications': [],
            'projects': []
        }
        
        # Upload resume
        pdf_file = SimpleUploadedFile(
            "john_doe_resume.pdf",
            b'%PDF-1.4 fake pdf content',
            content_type="application/pdf"
            
        )
        
        upload_url = reverse('resumes:resume-list-create')
        upload_response = self.client.post(upload_url, {'file': pdf_file}, format='multipart')
        
        self.assertEqual(upload_response.status_code, status.HTTP_201_CREATED)
        
        # Verify resume was created and parsed
        resume_id = upload_response.data['id']
        resume = Resume.objects.get(id=resume_id)
        
        self.assertEqual(resume.user, self.user)
        self.assertEqual(resume.original_filename, 'john_doe_resume.pdf')
        self.assertEqual(resume.file_type, 'pdf')
        self.assertTrue(resume.is_parsed)
        self.assertEqual(resume.full_name, 'John Doe')
        self.assertEqual(len(resume.skills), 4)
        self.assertEqual(len(resume.work_experience), 1)
        
        # Test listing resumes
        list_url = reverse('resumes:resume-list-create')
        list_response = self.client.get(list_url)
        
        self.assertEqual(list_response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(list_response.data['results']), 1)
        self.assertEqual(list_response.data['results'][0]['full_name'], 'John Doe')
        
        # Test getting detailed view
        detail_url = reverse('resumes:resume-detail', kwargs={'resume_id': resume_id})
        detail_response = self.client.get(detail_url)
        
        self.assertEqual(detail_response.status_code, status.HTTP_200_OK)
        self.assertEqual(detail_response.data['full_name'], 'John Doe')
        self.assertIn('extracted_text', detail_response.data)
        self.assertEqual(len(detail_response.data['skills']), 4)
    
    @patch('resumes.utils.extract_text_from_docx')
    def test_docx_upload_with_extraction_failure(self, mock_extract):
        """Test DOCX upload when text extraction fails"""
        mock_extract.side_effect = TextExtractionError("Could not extract text from DOCX")
        
        docx_file = SimpleUploadedFile(
            "broken_resume.docx",
            b'fake docx content',
            content_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )
        
        upload_url = reverse('resumes:resume-list-create')
        upload_response = self.client.post(upload_url, {'file': docx_file}, format='multipart')
        
        self.assertEqual(upload_response.status_code, status.HTTP_201_CREATED)
        
        # Resume should be created but not parsed
        resume_id = upload_response.data['id']
        resume = Resume.objects.get(id=resume_id)
        
        self.assertFalse(resume.is_parsed)
        self.assertIn("Text extraction failed:", resume.extracted_text)
        self.assertIsNotNone(resume.parsing_error)
    
    def test_multi_user_isolation(self):
        """Test that users can only access their own resumes"""
        # Create second user
        user2 = User.objects.create_user(
            username='user2',
            email='user2@example.com', 
            password='testpass123'
        )
        
        # Create resume for user1
        resume1 = Resume.objects.create(
            user=self.user,
            original_filename='user1_resume.pdf',
            file_type=Resume.PDF,
            file_size=1024
        )
        
        # Create resume for user2
        Resume.objects.create(
            user=user2,
            original_filename='user2_resume.pdf',
            file_type=Resume.PDF,
            file_size=1024
        )
        
        # User1 should only see their resume
        list_url = reverse('resumes:resume-list-create')
        list_response = self.client.get(list_url)
        
        self.assertEqual(len(list_response.data['results']), 1)
        self.assertEqual(list_response.data['results'][0]['original_filename'], 'user1_resume.pdf')
        
        # User1 should not be able to access user2's resume
        jwt_token2 = AccessToken.for_user(user2)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {str(jwt_token2)}')
        
        detail_url = reverse('resumes:resume-detail', kwargs={'resume_id': resume1.id})
        detail_response = self.client.get(detail_url)
        
        self.assertEqual(detail_response.status_code, status.HTTP_404_NOT_FOUND)


class ResumeConcurrencyTestCase(TransactionTestCase):
    """Test concurrent operations on resumes"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='concurrentuser',
            email='concurrent@example.com',
            password='testpass123'
        )
    
    def test_concurrent_resume_uploads(self):
        """Test handling of concurrent resume uploads"""
        import threading
        
        results = []
        errors = []
        
        def upload_resume(filename):
            try:
                resume = Resume.objects.create(
                    user=self.user,
                    original_filename=filename,
                    file_type=Resume.PDF,
                    file_size=1024,
                    extracted_text=f'Content for {filename}'
                )
                results.append(resume.id)
            except Exception as e:
                errors.append(str(e))
        
        # Create multiple threads to upload resumes concurrently
        threads = []
        for i in range(5):
            thread = threading.Thread(target=upload_resume, args=(f'resume_{i}.pdf',))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # All uploads should succeed
        self.assertEqual(len(errors), 0)
        self.assertEqual(len(results), 5)
        self.assertEqual(Resume.objects.filter(user=self.user).count(), 5)
