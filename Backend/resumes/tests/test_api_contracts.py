"""
API contract tests to ensure consistent API behavior
"""
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import AccessToken
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from ..models import Resume

User = get_user_model()


class ResumeAPIContractTestCase(APITestCase):
    """Test API contracts and response formats"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='apiuser',
            email='api@example.com',
            password='testpass123'
        )
        self.jwt_token = AccessToken.for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {str(self.jwt_token)}')
        
        self.resume = Resume.objects.create(
            user=self.user,
            original_filename='api_test_resume.pdf',
            file_type=Resume.PDF,
            file_size=1024,
            extracted_text='API test content',
            full_name='API Test User',
            contact_info={'email': 'api@test.com'},
            skills=['Python', 'Django'],
            is_parsed=True
        )
    
    def test_list_endpoint_response_structure(self):
        """Test list endpoint response structure"""
        url = reverse('resumes:resume-list-create')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        
        # Check response structure
        self.assertIn('results', response.data)
        self.assertIn('count', response.data)
        self.assertIn('next', response.data)
        self.assertIn('previous', response.data)
        
        # Check individual resume structure
        if response.data['results']:
            resume_data = response.data['results'][0]
            expected_fields = [
                'id', 'original_filename', 'file_type', 'file_size',
                'full_name', 'contact_email', 'contact_phone',
                'skills_display', 'is_parsed', 'uploaded_at', 'updated_at'
            ]
            
            for field in expected_fields:
                self.assertIn(field, resume_data)
    
    def test_detail_endpoint_response_structure(self):
        """Test detail endpoint response structure"""
        url = reverse('resumes:resume-detail', kwargs={'resume_id': self.resume.id})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        
        # Check all expected fields are present
        expected_fields = [
            'id', 'original_filename', 'file_type', 'file_size',
            'extracted_text', 'full_name', 'summary', 'contact_info',
            'contact_email', 'contact_phone', 'contact_linkedin',
            'skills', 'work_experience', 'education', 'certifications',
            'projects', 'is_parsed', 'parsing_error', 'uploaded_at',
            'updated_at', 'parsed_at', 'file_url'
        ]
        
        for field in expected_fields:
            self.assertIn(field, response.data)
        
        # Check data types
        self.assertIsInstance(response.data['id'], str)
        self.assertIsInstance(response.data['skills'], list)
        self.assertIsInstance(response.data['contact_info'], dict)
        self.assertIsInstance(response.data['is_parsed'], bool)
    
    def test_upload_endpoint_response_structure(self):
        """Test upload endpoint response structure"""
        pdf_file = SimpleUploadedFile(
            "contract_test.pdf",
            b'%PDF-1.4 fake content',
            content_type="application/pdf"
        )
        
        url = reverse('resumes:resume-list-create')
        response = self.client.post(url, {'file': pdf_file}, format='multipart')
        
        if response.status_code == 201:
            # Check response contains all expected fields from upload serializer
            expected_fields = [
                'id', 'original_filename', 'file_type', 'extracted_text',
                'full_name', 'summary', 'contact_info', 'skills',
                'work_experience', 'education', 'certifications',
                'projects', 'is_parsed', 'parsing_error', 'file_size',
                'uploaded_at', 'parsed_at'
            ]
            
            for field in expected_fields:
                self.assertIn(field, response.data)
    
    def test_error_response_structure(self):
        """Test error response structure consistency"""
        # Test 404 error
        fake_uuid = '00000000-0000-0000-0000-000000000000'
        url = reverse('resumes:resume-detail', kwargs={'resume_id': fake_uuid})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 404)
        self.assertIn('detail', response.data)
        
        # Test 400 error (invalid file upload)
        upload_url = reverse('resumes:resume-list-create')
        response = self.client.post(upload_url, {}, format='multipart')
        
        self.assertEqual(response.status_code, 400)
        # Should have field-specific errors
        self.assertIsInstance(response.data, dict)
    
    def test_pagination_consistency(self):
        """Test pagination consistency across list endpoints"""
        # Create multiple resumes
        for i in range(15):
            Resume.objects.create(
                user=self.user,
                original_filename=f'pagination_test_{i}.pdf',
                file_type=Resume.PDF,
                file_size=1024
            )
        
        url = reverse('resumes:resume-list-create')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        
        # Check pagination structure
        self.assertIn('results', response.data)
        self.assertIn('count', response.data)
        self.assertIn('next', response.data)
        self.assertIn('previous', response.data)
        
        # Check pagination metadata
        self.assertEqual(response.data['count'], 16)  # 15 + 1 existing
        self.assertIsInstance(response.data['results'], list)
    
    def test_content_type_headers(self):
        """Test that proper content type headers are returned"""
        url = reverse('resumes:resume-list-create')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/json')
    
    def test_http_methods_allowed(self):
        """Test that only allowed HTTP methods work"""
        list_url = reverse('resumes:resume-list-create')
        detail_url = reverse('resumes:resume-detail', kwargs={'resume_id': self.resume.id})
        
        # List endpoint should allow GET and POST
        get_response = self.client.get(list_url)
        self.assertNotEqual(get_response.status_code, 405)
        
        # POST should work (though may fail validation)
        post_response = self.client.post(list_url, {})
        self.assertNotEqual(post_response.status_code, 405)
        
        # Detail endpoint should allow GET
        detail_get_response = self.client.get(detail_url)
        self.assertNotEqual(detail_get_response.status_code, 405)
        
        # DELETE should not be allowed on detail endpoint (based on views)
        delete_response = self.client.delete(detail_url)
        self.assertEqual(delete_response.status_code, 405)
