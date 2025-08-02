"""
Performance tests for the resume application
"""
import time
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import AccessToken
from django.urls import reverse
from ..models import Resume

User = get_user_model()


class ResumePerformanceTestCase(APITestCase):
    """Test performance characteristics of resume operations"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='perfuser',
            email='perf@example.com',
            password='testpass123'
        )
        self.jwt_token = AccessToken.for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {str(self.jwt_token)}')
        
        # Create multiple resumes for testing
        self.resumes = []
        for i in range(50):
            resume = Resume.objects.create(
                user=self.user,
                original_filename=f'resume_{i}.pdf',
                file_type=Resume.PDF,
                file_size=1024 * (i + 1),
                extracted_text=f'Resume content {i}' * 100,  # Make it substantial
                full_name=f'User {i}',
                skills=[f'Skill_{j}' for j in range(i % 10 + 1)],
                is_parsed=True
            )
            self.resumes.append(resume)
    
    def test_resume_list_performance(self):
        """Test performance of listing many resumes"""
        url = reverse('resumes:resume-list-create')
        
        start_time = time.time()
        response = self.client.get(url)
        end_time = time.time()
        
        self.assertEqual(response.status_code, 200)
        self.assertLess(end_time - start_time, 2.0)  # Should complete within 2 seconds
    
    def test_resume_detail_performance(self):
        """Test performance of getting resume details"""
        resume = self.resumes[0]
        url = reverse('resumes:resume-detail', kwargs={'resume_id': resume.id})
        
        start_time = time.time()
        response = self.client.get(url)
        end_time = time.time()
        
        self.assertEqual(response.status_code, 200)
        self.assertLess(end_time - start_time, 1.0)  # Should complete within 1 second
    
    def test_multiple_resume_details_performance(self):
        """Test performance of getting multiple resume details"""
        start_time = time.time()
        
        for resume in self.resumes[:10]:  # Test first 10 resumes
            url = reverse('resumes:resume-detail', kwargs={'resume_id': resume.id})
            response = self.client.get(url)
            self.assertEqual(response.status_code, 200)
        
        end_time = time.time()
        self.assertLess(end_time - start_time, 5.0)  # Should complete within 5 seconds
    
    def test_database_query_optimization(self):
        """Test that database queries are optimized"""
        from django.test.utils import override_settings
        from django.db import connection
        
        with override_settings(DEBUG=True):
            connection.queries_log.clear()
            
            url = reverse('resumes:resume-list-create')
            response = self.client.get(url)
            
            self.assertEqual(response.status_code, 200)
            # Should not have excessive database queries
            self.assertLess(len(connection.queries), 10)