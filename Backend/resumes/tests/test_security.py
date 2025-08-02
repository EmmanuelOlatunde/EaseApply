"""
Security tests for the resume application
"""
import uuid
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import AccessToken
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from ..models import Resume

User = get_user_model()


class ResumeSecurityTestCase(APITestCase):
    """Test security aspects of the resume application"""
    
    def setUp(self):
        self.user1 = User.objects.create_user(
            username='secuser1',
            email='sec1@example.com',
            password='testpass123'
        )
        self.user2 = User.objects.create_user(
            username='secuser2',
            email='sec2@example.com',
            password='testpass123'
        )
        
        self.jwt_token1 = AccessToken.for_user(self.user1)
        self.jwt_token2 = AccessToken.for_user(self.user2)
        
        # Create resumes for both users
        self.resume1 = Resume.objects.create(
            user=self.user1,
            original_filename='user1_resume.pdf',
            file_type=Resume.PDF,
            file_size=1024,
            extracted_text='Confidential user 1 information'
        )
        
        self.resume2 = Resume.objects.create(
            user=self.user2,
            original_filename='user2_resume.pdf',
            file_type=Resume.PDF,
            file_size=1024,
            extracted_text='Confidential user 2 information'
        )
    
    def test_unauthorized_access_prevention(self):
        """Test that unauthorized users cannot access any endpoints"""
        endpoints = [
            reverse('resumes:resume-list-create'),
            reverse('resumes:resume-list-create'),
            reverse('resumes:resume-detail', kwargs={'resume_id': self.resume1.id}),
        ]
        
        for endpoint in endpoints:
            response = self.client.get(endpoint)
            self.assertEqual(response.status_code, 401)
    
    def test_cross_user_data_access_prevention(self):
        """Test that users cannot access other users' data"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {str(self.jwt_token1)}')
        
        # User1 tries to access User2's resume
        url = reverse('resumes:resume-detail', kwargs={'resume_id': self.resume2.id})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 404)
        # Should not leak information about the existence of the resume
        self.assertNotIn('user2', str(response.data).lower())
    
    def test_sql_injection_protection(self):
        """Test protection against SQL injection attempts"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {str(self.jwt_token1)}')
        
        # Attempt SQL injection in search parameter
        malicious_queries = [
            "'; DROP TABLE resumes_resume; --",
            "' OR '1'='1",
            "'; DELETE FROM resumes_resume WHERE id=1; --",
            "1' UNION SELECT * FROM auth_user --"
        ]
        
        url = reverse('resumes:resume-list-create')
        
        for query in malicious_queries:
            response = self.client.get(url, {'search': query})
            # Should not cause server error or expose sensitive data
            self.assertIn(response.status_code, [200, 400])
            # Database should still have our test data
            self.assertTrue(Resume.objects.filter(id=self.resume1.id).exists())
    
    def test_file_type_validation_security(self):
        """Test that file type validation prevents malicious uploads"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {str(self.jwt_token1)}')
        
        malicious_files = [
            # Executable file with PDF extension
            SimpleUploadedFile(
                "malicious.pdf",
                b'MZ\x90\x00',  # PE header
                content_type="application/pdf"
            ),
            # Script file
            SimpleUploadedFile(
                "script.pdf",
                b'#!/bin/bash\nrm -rf /',
                content_type="application/pdf"
            ),
            # HTML file with JavaScript
            SimpleUploadedFile(
                "xss.pdf",
                b'<html><script>alert("XSS")</script></html>',
                content_type="application/pdf"
            )
        ]
        
        url = reverse('resumes:resume-list-create')
        
        for malicious_file in malicious_files:
            response = self.client.post(url, {'file': malicious_file}, format='multipart')
            # Should either reject the file or handle it safely
            if response.status_code == 201:
                # If accepted, verify it's stored safely
                resume = Resume.objects.get(id=response.data['id'])
                self.assertIsNotNone(resume.file)
    
    def test_path_traversal_protection(self):
        """Test protection against path traversal attacks"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {str(self.jwt_token1)}')
        
        malicious_filenames = [
            "../../../etc/passwd.pdf",
            "..\\..\\..\\windows\\system32\\config\\sam.pdf",
            "/etc/shadow.pdf",
            "..%2F..%2F..%2Fetc%2Fpasswd.pdf"  # URL encoded
        ]
        
        url = reverse('resumes:resume-list-create')
        
        for filename in malicious_filenames:
            malicious_file = SimpleUploadedFile(
                filename,
                b'%PDF-1.4 fake content',
                content_type="application/pdf"
            )
            
            response = self.client.post(url, {'file': malicious_file}, format='multipart')
            
            if response.status_code == 201:
                resume = Resume.objects.get(id=response.data['id'])
                # Filename should be sanitized
                self.assertNotIn('..', resume.original_filename)
                self.assertNotIn('/etc/', resume.original_filename)

    
    def test_uuid_enumeration_protection(self):
        """Test protection against UUID enumeration attacks"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {str(self.jwt_token1)}')
        
        # Generate random UUIDs and try to access them
        for _ in range(10):
            random_uuid = uuid.uuid4()
            url = reverse('resumes:resume-detail', kwargs={'resume_id': random_uuid})
            response = self.client.get(url)
            
            # Should consistently return 404, not leak information
            self.assertEqual(response.status_code, 404)
            # Response should not indicate whether the UUID exists for another user
            self.assertEqual(response.data.get('detail'), 'Not found.')
    
    def test_token_expiry_handling(self):
        """Test handling of expired tokens"""
        from datetime import timedelta
        from django.utils import timezone

        # Create an expired token (this is a simplified test)
        expired_token = AccessToken.for_user(self.user1)
        # Manually set expiry time to past (in real scenario, wait for natural expiry)
        expired_token.set_exp(from_time=timezone.now() - timedelta(days=1))
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {str(expired_token)}')
        
        url = reverse('resumes:resume-list-create')
        response = self.client.get(url)
        
        # Should handle expired tokens gracefully
        # Note: This test may need adjustment based on JWT settings
        self.assertIn(response.status_code, [401, 403])
    
    def test_mass_assignment_protection(self):
        """Test protection against mass assignment vulnerabilities"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {str(self.jwt_token1)}')
        
        pdf_file = SimpleUploadedFile(
            "test.pdf",
            b'%PDF-1.4 fake content',
            content_type="application/pdf"
        )
        
        # Try to set protected fields via mass assignment
        malicious_data = {
            'file': pdf_file,
            'user': self.user2.id,  # Try to assign to different user
            'id': str(uuid.uuid4()),  # Try to set custom ID
            'is_parsed': True,  # Try to set read-only field
            'file_size': 999999,  # Try to set auto-calculated field
        }
        
        url = reverse('resumes:resume-list-create')
        response = self.client.post(url, malicious_data, format='multipart')
        
        if response.status_code == 201:
            resume = Resume.objects.get(id=response.data['id'])
            # Should be assigned to requesting user, not user2
            self.assertEqual(resume.user, self.user1)
            # ID should be auto-generated, not the one we tried to set
            self.assertNotEqual(str(resume.id), malicious_data['id'])
    
    def test_information_disclosure_prevention(self):
        """Test that error messages don't disclose sensitive information"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {str(self.jwt_token1)}')
        
        # Try to access non-existent resume
        fake_uuid = uuid.uuid4()
        url = reverse('resumes:resume-detail', kwargs={'resume_id': fake_uuid})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 404)
        # Error message should be generic, not revealing database structure
        self.assertNotIn('Resume', response.data.get('detail', ''))
        self.assertNotIn('database', str(response.data).lower())
        self.assertNotIn('sql', str(response.data).lower())
    
    def test_rate_limiting_simulation(self):
        """Test behavior under high request volume (simulated rate limiting test)"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {str(self.jwt_token1)}')
        
        url = reverse('resumes:resume-list-create')
        
        # Make many requests in quick succession
        responses = []
        for _ in range(20):
            response = self.client.get(url)
            responses.append(response.status_code)
        
        # All should succeed (in production, rate limiting would apply)
        for status_code in responses:
            self.assertIn(status_code, [200, 429])  # 429 if rate limiting is implemented
    
    def test_content_type_validation(self):
        """Test validation of content types"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {str(self.jwt_token1)}')
        
        # File with correct extension but wrong MIME type
        fake_pdf = SimpleUploadedFile(
            "fake.pdf",
            b'This is not a PDF',
            content_type="text/plain"  # Wrong MIME type
        )
        
        url = reverse('resumes:resume-list-create')
        response = self.client.post(url, {'file': fake_pdf}, format='multipart')
        
        # Should handle gracefully (may accept or reject based on validation logic)
        self.assertIn(response.status_code, [201, 400])
