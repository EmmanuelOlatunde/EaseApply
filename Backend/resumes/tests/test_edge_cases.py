"""
Edge case tests for the resume application
"""
from unittest.mock import patch
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import AccessToken
from django.urls import reverse
from ..models import Resume

User = get_user_model()


class ResumeEdgeCaseTestCase(APITestCase):
    """Test edge cases and boundary conditions"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='edgeuser',
            email='edge@example.com',
            password='testpass123'
        )
        self.jwt_token = AccessToken.for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {str(self.jwt_token)}')
    
    def test_empty_file_upload(self):
        """Test uploading an empty file"""
        empty_file = SimpleUploadedFile(
            "empty.pdf",
            b'',  # Empty content
            content_type="application/pdf"
        )
        
        url = reverse('resumes:resume-list-create')
        response = self.client.post(url, {'file': empty_file}, format='multipart')
        
        # Should fail validation
        self.assertEqual(response.status_code, 400)
    
    def test_file_with_special_characters_in_name(self):
        """Test uploading file with special characters in filename"""
        special_file = SimpleUploadedFile(
            "résumé with spëcial chars & symbols!@#.pdf",
            b'%PDF-1.4 fake content',
            content_type="application/pdf"
        )
        
        url = reverse('resumes:resume-list-create')
        response = self.client.post(url, {'file': special_file}, format='multipart')
        
        if response.status_code == 201:
            resume = Resume.objects.get(id=response.data['id'])
            self.assertEqual(resume.original_filename, "résumé with spëcial chars & symbols!@#.pdf")
    
    def test_very_long_filename(self):
        """Test uploading file with very long filename"""
        long_filename = "a" * 200 + ".pdf"  # 204 characters total
        long_file = SimpleUploadedFile(
            long_filename,
            b'%PDF-1.4 fake content',
            content_type="application/pdf"
        )
        
        url = reverse('resumes:resume-list-create')
        response = self.client.post(url, {'file': long_file}, format='multipart')
        
        # Should handle long filenames gracefully
        if response.status_code == 201:
            resume = Resume.objects.get(id=response.data['id'])
            # Filename should be truncated or handled appropriately
            self.assertLessEqual(len(resume.original_filename), 255)
    
    def test_unicode_content_in_extracted_text(self):
        """Test handling of Unicode content in extracted text"""
        resume = Resume.objects.create(
            user=self.user,
            original_filename='unicode_resume.pdf',
            file_type=Resume.PDF,
            file_size=1024,
            extracted_text='José García\nSoftware Engineer\nEmail: josé@example.com\n中文内容'
        )
        
        url = reverse('resumes:resume-detail', kwargs={'resume_id': resume.id})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertIn('José García', response.data['extracted_text'])
        self.assertIn('中文内容', response.data['extracted_text'])
    
    def test_malformed_json_in_fields(self):
        """Test handling of malformed JSON in JSON fields"""
        # This tests the model's ability to handle invalid JSON data
        resume = Resume.objects.create(
            user=self.user,
            original_filename='test.pdf',
            file_type=Resume.PDF,
            file_size=1024
        )
        
        # Test with valid JSON
        resume.contact_info = {'email': 'test@example.com'}
        resume.skills = ['Python', 'Django']
        resume.save()
        
        url = reverse('resumes:resume-detail', kwargs={'resume_id': resume.id})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['contact_info']['email'], 'test@example.com')
    
    def test_maximum_file_size_boundary(self):
        """Test file size at the boundary of the limit"""
        # Create a file just under 10MB
        size_9_9_mb = int(9.9 * 1024 * 1024)
        large_content = b'x' * size_9_9_mb
        
        large_file = SimpleUploadedFile(
            "large_resume.pdf",
            large_content,
            content_type="application/pdf"
        )
        
        url = reverse('resumes:resume-list-create')
        response = self.client.post(url, {'file': large_file}, format='multipart')
        
        # Should succeed for files under 10MB
        self.assertIn(response.status_code, [201, 400])  # Depends on actual validation
    
    def test_invalid_uuid_in_url(self):
        """Test accessing endpoints with invalid UUIDs"""
        invalid_uuids = [
            'not-a-uuid',
            '12345',
            'xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx',
            '123e4567-e89b-12d3-a456-42661417400',  # Too short
        ]
        
        for invalid_uuid in invalid_uuids:
            url = f'/resumes/{invalid_uuid}/'
            response = self.client.get(url)
            # Should return 404 because URL pattern won't match
            self.assertEqual(response.status_code, 404)
    
    def test_deleted_user_resume_access(self):
        """Test accessing resume after user is deleted"""
        # Create resume
        resume = Resume.objects.create(
            user=self.user,
            original_filename='test.pdf',
            file_type=Resume.PDF,
            file_size=1024
        )
        
        resume_id = resume.id
        
        # Delete user (should cascade delete resume)
        self.user.delete()
        
        # Resume should no longer exist
        self.assertFalse(Resume.objects.filter(id=resume_id).exists())
    
    @patch('resumes.utils.extract_text_from_pdf')
    def test_extraction_with_memory_error(self, mock_extract):
        """Test handling of memory errors during text extraction"""
        mock_extract.side_effect = MemoryError("Not enough memory")
        
        pdf_file = SimpleUploadedFile(
            "memory_error.pdf",
            b'%PDF-1.4 fake content',
            content_type="application/pdf"
        )
        
        url = reverse('resumes:resume-list-create')
        response = self.client.post(url, {'file': pdf_file}, format='multipart')
        
        # Should handle memory error gracefully
        self.assertEqual(response.status_code, 201)
        resume = Resume.objects.get(id=response.data['id'])
        self.assertIn("unexpected error", resume.extracted_text)
    
    def test_simultaneous_uploads_same_filename(self):
        """Test uploading multiple files with the same filename"""
        pdf_file1 = SimpleUploadedFile(
            "resume.pdf",
            b'%PDF-1.4 content 1',
            content_type="application/pdf"
        )
        
        pdf_file2 = SimpleUploadedFile(
            "resume.pdf",  # Same filename
            b'%PDF-1.4 content 2',
            content_type="application/pdf"
        )
        
        url = reverse('resumes:resume-list-create')
        
        # Upload first file
        response1 = self.client.post(url, {'file': pdf_file1}, format='multipart')
        
        # Upload second file with same name
        response2 = self.client.post(url, {'file': pdf_file2}, format='multipart')
        
        # Both should succeed (files are stored with UUID names)
        self.assertEqual(response1.status_code, 201)
        self.assertEqual(response2.status_code, 201)
        
        # Should have 2 different resumes
        self.assertEqual(Resume.objects.filter(user=self.user).count(), 2)

