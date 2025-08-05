"""
Integration tests for the Analysis app.
Tests complete workflows from API request to database storage.
"""

from django.test import TransactionTestCase
from rest_framework import status
from unittest.mock import patch
from resumes.models import Resume

from analysis.models import AnalysisResult
from .test_base import BaseAnalysisTestCase, MockServiceMixin, TestDataFactory, AssertionHelpers


class CoverLetterGenerationIntegrationTest(BaseAnalysisTestCase, MockServiceMixin):
    """Integration tests for complete cover letter generation workflow."""
    
    def test_complete_workflow_with_provided_ids(self):
        """Test complete workflow from request to database storage with provided IDs."""
        # Arrange
        initial_count = AnalysisResult.objects.count()
        
        request_data = {
            'job_id': self.job_description.id,
            'resume_id': self.resume.id,
            'template_type': 'professional'
        }
        
        mock_service_response = {
            'success': True,
            'cover_letter': 'Dear Hiring Manager,\n\nI am excited to apply for the Senior Software Engineer position...',
            'prompt_used': 'You are an expert cover letter writer...',
            'metadata': {
                'model': 'gpt-4o-mini',
                'tokens_used': 650,
                'processing_time': 2.3,
                'template_type': 'professional'
            }
        }
        
        # Act
        with self.patch_openrouter_service(return_value=mock_service_response):
            response = self.client.post(self.cover_letter_url, request_data)
        
        # Assert
        self.assert_successful_response(response)
        
        # Verify response structure and content
        data = response.json()
        self.assertEqual(data['success'], True)
        self.assertIn('Dear Hiring Manager', data['cover_letter'])
        self.assertIsInstance(data['analysis_id'], int)
        
        # Verify metadata
        metadata = data['metadata']
        self.assertEqual(metadata['job_title'], self.job_description.title)
        self.assertEqual(metadata['processing_time'], 2.3)
        self.assertEqual(metadata['tokens_used'], 650)
        self.assertEqual(metadata['model_used'], 'gpt-4o-mini')
        AssertionHelpers.assert_timestamp_recent(self, metadata['created_at'])
        
        # Verify database record
        self.assertEqual(AnalysisResult.objects.count(), initial_count + 1)
        
        analysis = AnalysisResult.objects.get(id=data['analysis_id'])
        self.assertEqual(analysis.user, self.user)
        self.assertEqual(analysis.job_description, self.job_description)
        self.assertEqual(analysis.resume, self.resume)
        self.assertEqual(analysis.analysis_type, 'cover_letter')
        self.assertIn('Dear Hiring Manager', analysis.result_text)
        self.assertEqual(analysis.model_used, 'gpt-4o-mini')
        self.assertEqual(analysis.tokens_used, 650)
        self.assertEqual(analysis.processing_time, 2.3)
        self.assertIn('You are an expert cover letter writer', analysis.prompt_used)
    
    def test_complete_workflow_without_ids(self):
        """Test complete workflow using latest job and resume when no IDs provided."""
        # Create multiple jobs and resumes to test selection logic
        TestDataFactory.create_multiple_jobs(self.user, count=2)
        TestDataFactory.create_multiple_resumes(self.user, count=2)
        
        # Create newest job and resume that should be selected
        newest_job = self.create_job_description(title='Latest Job Position')
        newest_resume = self.create_resume(title='Latest Resume')
        
        request_data = {'template_type': 'creative'}
        
        # Act
        with self.patch_openrouter_service():
            response = self.client.post(self.cover_letter_url, request_data)
        
        # Assert
        self.assert_successful_response(response)
        
        # Verify correct job and resume were used
        data = response.json()
        analysis = AnalysisResult.objects.get(id=data['analysis_id'])
        
        self.assertEqual(analysis.job_description, newest_job)
        self.assertEqual(analysis.resume, newest_resume)
        self.assertEqual(data['metadata']['job_title'], 'Latest Job Position')
    
    def test_end_to_end_with_realistic_data(self):
        """Test end-to-end workflow with realistic job and resume data."""
        # Create realistic job description
        realistic_job = self.create_job_description(
            title='Full Stack Developer',
            company='Innovative Tech Solutions',
            location='Seattle, WA',
            job_type='Full-time',
            salary_range='$110,000 - $140,000',
            requirements='''
            We are seeking a Full Stack Developer with 3+ years of experience.
            Must have strong proficiency in JavaScript, React, Node.js, and Python.
            Experience with AWS, Docker, and microservices architecture preferred.
            Bachelor's degree in Computer Science or equivalent experience required.
            ''',
            skills_required='JavaScript, React, Node.js, Python, AWS, Docker, PostgreSQL',
            experience_level='Mid'
        )
        
        # Create realistic resume
        realistic_resume = self.create_resume(
            title='Full Stack Developer Resume',
            extracted_text='''
            Jane Developer
            Full Stack Developer
            jane.developer@email.com | LinkedIn: /in/janedev
            
            PROFESSIONAL EXPERIENCE
            
            Software Developer | TechStart Inc. | 2021 - Present
            • Developed and maintained full-stack web applications using React and Node.js
            • Built RESTful APIs serving 500k+ monthly active users
            • Implemented microservices architecture reducing system latency by 35%
            • Collaborated with UX/UI designers to create responsive web interfaces
            • Utilized AWS services including EC2, S3, and RDS for cloud deployment
            
            Junior Developer | Digital Solutions Co. | 2019 - 2021
            • Created dynamic web applications using JavaScript, HTML, and CSS
            • Integrated third-party APIs and payment processing systems
            • Optimized database queries improving application performance by 25%
            • Participated in code reviews and agile development processes
            
            EDUCATION
            Bachelor of Science in Computer Science
            University of Washington | 2019
            
            TECHNICAL SKILLS
            Languages: JavaScript, Python, TypeScript, SQL
            Frameworks: React, Node.js, Express, Django
            Databases: PostgreSQL, MongoDB, Redis
            Cloud: AWS (EC2, S3, RDS), Docker, Kubernetes
            Tools: Git, Jenkins, JIRA, Postman
            '''
        )
        
        mock_realistic_response = {
            'success': True,
            'cover_letter': '''Dear Hiring Manager,

I am writing to express my strong interest in the Full Stack Developer position at Innovative Tech Solutions. With over 4 years of experience developing scalable web applications and a proven track record of delivering high-quality solutions, I am excited about the opportunity to contribute to your innovative team.

In my current role at TechStart Inc., I have successfully developed and maintained full-stack applications using React and Node.js that serve over 500,000 monthly active users. My experience implementing microservices architecture resulted in a 35% reduction in system latency, directly improving user experience. Additionally, my proficiency with AWS services including EC2, S3, and RDS aligns perfectly with your preferred qualifications.

What particularly draws me to Innovative Tech Solutions is your commitment to cutting-edge technology and innovation. I am eager to bring my expertise in JavaScript, Python, and cloud technologies to help drive your projects forward while continuing to grow in a collaborative environment.

I would welcome the opportunity to discuss how my technical skills and passion for full-stack development can contribute to your team's success. Thank you for considering my application.

Sincerely,
Jane Developer''',
            'prompt_used': 'Professional cover letter prompt...',
            'metadata': {
                'model': 'claude-3-sonnet',
                'tokens_used': 425,
                'processing_time': 1.8,
                'template_type': 'professional'
            }
        }
        
        # Act
        with self.patch_openrouter_service(return_value=mock_realistic_response):
            response = self.client.post(self.cover_letter_url, {
                'job_id': realistic_job.id,
                'resume_id': realistic_resume.id,
                'template_type': 'professional'
            })
        
        # Assert
        self.assert_successful_response(response)
        
        data = response.json()
        
        # Verify realistic content integration
        cover_letter = data['cover_letter']
        self.assertIn('Full Stack Developer', cover_letter)
        self.assertIn('Innovative Tech Solutions', cover_letter)
        self.assertIn('500,000 monthly active users', cover_letter)
        self.assertIn('35% reduction in system latency', cover_letter)
        self.assertIn('Jane Developer', cover_letter)
        
        # Verify complete database integration
        analysis = AnalysisResult.objects.get(id=data['analysis_id'])
        self.assertEqual(analysis.job_description, realistic_job)
        self.assertEqual(analysis.resume, realistic_resume)
        self.assertIn('TechStart Inc.', analysis.prompt_used)  # Resume content in prompt
        self.assertIn('Innovative Tech Solutions', analysis.prompt_used)  # Job content in prompt
    
    def test_concurrent_requests_isolation(self):
        """Test that concurrent requests from same user create separate records."""
        # Create multiple job descriptions and resumes
        job1 = self.create_job_description(title='Job 1')
        job2 = self.create_job_description(title='Job 2')
        resume1 = self.create_resume(title='Resume 1')
        resume2 = self.create_resume(title='Resume 2')
        
        mock_response1 = self.get_successful_service_response('Cover letter 1')
        mock_response2 = self.get_successful_service_response('Cover letter 2')
        
        # Simulate concurrent requests
        with patch('analysis.services.OpenRouterService.generate_cover_letter') as mock_service:
            mock_service.side_effect = [mock_response1, mock_response2]
            
            response1 = self.client.post(self.cover_letter_url, {
                'job_id': job1.id,
                'resume_id': resume1.id
            })
            
            response2 = self.client.post(self.cover_letter_url, {
                'job_id': job2.id,
                'resume_id': resume2.id
            })
        
        # Both requests should succeed
        self.assert_successful_response(response1)
        self.assert_successful_response(response2)
        
        # Should create separate database records
        data1 = response1.json()
        data2 = response2.json()
        
        self.assertNotEqual(data1['analysis_id'], data2['analysis_id'])
        self.assertEqual(data1['cover_letter'], 'Cover letter 1')
        self.assertEqual(data2['cover_letter'], 'Cover letter 2')
        
        # Verify database records
        analysis1 = AnalysisResult.objects.get(id=data1['analysis_id'])
        analysis2 = AnalysisResult.objects.get(id=data2['analysis_id'])
        
        self.assertEqual(analysis1.job_description, job1)
        self.assertEqual(analysis2.job_description, job2)
        self.assertEqual(analysis1.resume, resume1)
        self.assertEqual(analysis2.resume, resume2)
    
    def test_multiple_user_isolation(self):
        """Test that requests from different users are properly isolated."""
        # Create data for second user
        other_job = self.create_job_description(user=self.other_user, title='Other User Job')
        other_resume = self.create_resume(user=self.other_user, title='Other User Resume')
        
        # First user request
        with self.patch_openrouter_service(return_value=self.get_successful_service_response('User 1 letter')):
            response1 = self.client.post(self.cover_letter_url, {
                'job_id': self.job_description.id,
                'resume_id': self.resume.id
            })
        
        # Switch to second user
        self.authenticate_user(self.other_user)
        
        # Second user request
        with self.patch_openrouter_service(return_value=self.get_successful_service_response('User 2 letter')):
            response2 = self.client.post(self.cover_letter_url, {
                'job_id': other_job.id,
                'resume_id': other_resume.id
            })
        
        # Both should succeed
        self.assert_successful_response(response1)
        self.assert_successful_response(response2)
        
        # Verify proper user isolation in database
        data1 = response1.json()
        data2 = response2.json()
        
        analysis1 = AnalysisResult.objects.get(id=data1['analysis_id'])
        analysis2 = AnalysisResult.objects.get(id=data2['analysis_id'])
        
        self.assertEqual(analysis1.user, self.user)
        self.assertEqual(analysis2.user, self.other_user)
        self.assertEqual(analysis1.cover_letter, 'User 1 letter')
        self.assertEqual(analysis2.cover_letter, 'User 2 letter')
    
    def test_error_rollback_integration(self):
        """Test that database transactions are properly rolled back on errors."""
        initial_count = AnalysisResult.objects.count()
        
        # Mock service to succeed but database save to fail
        with self.patch_openrouter_service():
            with patch('analysis.models.AnalysisResult.objects.create') as mock_create:
                mock_create.side_effect = Exception('Database error')
                
                response = self.client.post(self.cover_letter_url, {
                    'job_id': self.job_description.id,
                    'resume_id': self.resume.id
                })
        
        # Should return error
        self.assert_error_response(response, status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        # No new records should be created
        self.assertEqual(AnalysisResult.objects.count(), initial_count)
    
    def test_service_failure_no_database_changes(self):
        """Test that service failures don't create incomplete database records."""
        initial_count = AnalysisResult.objects.count()
        
        # Mock service to fail
        failed_response = self.get_failed_service_response('Service unavailable')
        
        with self.patch_openrouter_service(return_value=failed_response):
            response = self.client.post(self.cover_letter_url, {
                'job_id': self.job_description.id,
                'resume_id': self.resume.id
            })
        
        # Should return error
        self.assert_error_response(response, status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        # No database records should be created
        self.assertEqual(AnalysisResult.objects.count(), initial_count)


class DataConsistencyIntegrationTest(BaseAnalysisTestCase, MockServiceMixin):
    """Integration tests for data consistency and integrity."""
    
    def test_prompt_data_consistency(self):
        """Test that prompt contains all provided job and resume data."""
        detailed_job = self.create_job_description(
            title='Data Scientist',
            company='AI Research Lab',
            location='Boston, MA',
            job_type='Contract',
            salary_range='$150,000 - $180,000',
            requirements='PhD in Statistics, 5+ years ML experience',
            skills_required='Python, TensorFlow, PyTorch, SQL',
            experience_level='Senior'
        )
        
        detailed_resume = self.create_resume(
            title='Data Scientist Resume',
            extracted_text='PhD Statistics, 7 years ML experience, expert in Python, TensorFlow'
        )
        
        # Capture the actual service call to verify prompt content
        captured_prompt = None
        
        def capture_service_call(*args, **kwargs):
            nonlocal captured_prompt
            # The prompt is formatted in the view, but we can capture the parameters
            # that should be in the prompt
            captured_prompt = {
                'title': kwargs.get('title'),
                'company': kwargs.get('company'),
                'location': kwargs.get('location'),
                'job_type': kwargs.get('job_type'),
                'salary_range': kwargs.get('salary_range'),
                'requirements': kwargs.get('requirements'),
                'skills_required': kwargs.get('skills_required'),
                'experience_level': kwargs.get('experience_level'),
                'resume_content': kwargs.get('resume_content'),
                'template_type': kwargs.get('template_type')
            }
            return self.get_successful_service_response()
        
        with patch('analysis.services.OpenRouterService.generate_cover_letter', 
                  side_effect=capture_service_call):
            response = self.client.post(self.cover_letter_url, {
                'job_id': detailed_job.id,
                'resume_id': detailed_resume.id,
                'template_type': 'creative'
            })
        
        self.assert_successful_response(response)
        
        # Verify all data was passed to service
        self.assertEqual(captured_prompt['title'], 'Data Scientist')
        self.assertEqual(captured_prompt['company'], 'AI Research Lab')
        self.assertEqual(captured_prompt['location'], 'Boston, MA')
        self.assertEqual(captured_prompt['job_type'], 'Contract')
        self.assertEqual(captured_prompt['salary_range'], '$150,000 - $180,000')
        self.assertEqual(captured_prompt['requirements'], 'PhD in Statistics, 5+ years ML experience')
        self.assertEqual(captured_prompt['skills_required'], 'Python, TensorFlow, PyTorch, SQL')
        self.assertEqual(captured_prompt['experience_level'], 'Senior')
        self.assertIn('PhD Statistics', captured_prompt['resume_content'])
        self.assertEqual(captured_prompt['template_type'], 'creative')
    
    def test_metadata_consistency_across_layers(self):
        """Test that metadata is consistent from service to API response to database."""
        service_metadata = {
            'model': 'test-model-consistent',
            'tokens_used': 567,
            'processing_time': 4.2,
            'template_type': 'professional'
        }
        
        service_response = {
            'success': True,
            'cover_letter': 'Consistent cover letter',
            'prompt_used': 'Consistent prompt',
            'metadata': service_metadata
        }
        
        with self.patch_openrouter_service(return_value=service_response):
            response = self.client.post(self.cover_letter_url, {
                'job_id': self.job_description.id,
                'resume_id': self.resume.id,
                'template_type': 'professional'
            })
        
        self.assert_successful_response(response)
        
        # Check API response metadata
        api_data = response.json()
        api_metadata = api_data['metadata']
        
        self.assertEqual(api_metadata['model_used'], 'test-model-consistent')
        self.assertEqual(api_metadata['tokens_used'], 567)
        self.assertEqual(api_metadata['processing_time'], 4.2)
        
        # Check database metadata
        analysis = AnalysisResult.objects.get(id=api_data['analysis_id'])
        
        self.assertEqual(analysis.model_used, 'test-model-consistent')
        self.assertEqual(analysis.tokens_used, 567)
        self.assertEqual(analysis.processing_time, 4.2)
        self.assertEqual(analysis.result_text, 'Consistent cover letter')
        self.assertEqual(analysis.prompt_used, 'Consistent prompt')
    
    def test_user_data_isolation_integrity(self):
        """Test that user data isolation is maintained across all operations."""
        # Create jobs and resumes for both users
        user1_job = self.create_job_description(user=self.user, title='User 1 Job')
        user1_resume = self.create_resume(user=self.user, title='User 1 Resume')
        
        user2_job = self.create_job_description(user=self.other_user, title='User 2 Job')
        user2_resume = self.create_resume(user=self.other_user, title='User 2 Resume')
        
        # User 1 creates analysis
        with self.patch_openrouter_service(return_value=self.get_successful_service_response('Letter 1')):
            response1 = self.client.post(self.cover_letter_url, {
                'job_id': user1_job.id,
                'resume_id': user1_resume.id
            })
        
        # Switch to user 2 and create analysis
        self.authenticate_user(self.other_user)
        
        with self.patch_openrouter_service(return_value=self.get_successful_service_response('Letter 2')):
            response2 = self.client.post(self.cover_letter_url, {
                'job_id': user2_job.id,
                'resume_id': user2_resume.id
            })
        
        # Verify complete isolation
        data1 = response1.json()
        data2 = response2.json()
        
        analysis1 = AnalysisResult.objects.get(id=data1['analysis_id'])
        analysis2 = AnalysisResult.objects.get(id=data2['analysis_id'])
        
        # User 1's analysis should only reference user 1's data
        self.assertEqual(analysis1.user, self.user)
        self.assertEqual(analysis1.job_description.user, self.user)
        self.assertEqual(analysis1.resume.user, self.user)
        
        # User 2's analysis should only reference user 2's data
        self.assertEqual(analysis2.user, self.other_user)
        self.assertEqual(analysis2.job_description.user, self.other_user)
        self.assertEqual(analysis2.resume.user, self.other_user)
        
        # Content should be different
        self.assertEqual(analysis1.result_text, 'Letter 1')
        self.assertEqual(analysis2.result_text, 'Letter 2')


class PerformanceIntegrationTest(TransactionTestCase):
    """Performance-focused integration tests."""
    
    def setUp(self):
        # Use TransactionTestCase for database transaction testing
        from django.contrib.auth import get_user_model
        from jobs.models import JobDescription
        from resumes.models import Resume
        
        User = get_user_model()
        
        self.user = User.objects.create_user(
            username='perfuser',
            email='perf@example.com',
            password='testpass123'
        )
        
        self.job = JobDescription.objects.create(
            title='Performance Test Job',
            company='Performance Corp',
            location='Test City',
            job_type='Full-time',
            salary_range='$100k',
            requirements='Performance requirements',
            skills_required='Performance skills',
            experience_level='Mid',
            user=self.user
        )
        
        self.resume = Resume.objects.create(
            title='Performance Resume',
            extracted_text='Performance resume content',
            user=self.user
        )
    
    def test_database_transaction_performance(self):
        """Test that database operations are performed efficiently."""
        from django.test.utils import override_settings
        from django.db import connection
        
        # Track database queries
        with override_settings(DEBUG=True):
            from rest_framework.test import APIClient
            
            client = APIClient()
            client.force_authenticate(user=self.user)
            
            # Reset query log
            connection.queries_log.clear()
            
            with patch('analysis.services.OpenRouterService.generate_cover_letter') as mock_service:
                mock_service.return_value = {
                    'success': True,
                    'cover_letter': 'Performance test letter',
                    'prompt_used': 'Performance prompt',
                    'metadata': {
                        'model': 'perf-model',
                        'tokens_used': 400,
                        'processing_time': 1.5,
                        'template_type': 'professional'
                    }
                }
                
                response = client.post('/analysis/generate-cover-letter/', {
                    'job_id': self.job.id,
                    'resume_id': self.resume.id
                })
            
            # Verify successful response
            self.assertEqual(response.status_code, 201)
            
            # Check that database queries are reasonable (not N+1 queries)
            # We expect: user lookup, job lookup, resume lookup, analysis creation
            # Plus some auth-related queries
            query_count = len(connection.queries)
            self.assertLess(query_count, 15, f"Too many database queries: {query_count}")
    
    def test_large_resume_content_handling(self):
        """Test handling of very large resume content."""
        from rest_framework.test import APIClient
        
        # Create resume with large content
        large_content = "Large resume content. " * 5000  # ~100KB content
        large_resume = Resume.objects.create(
            title='Large Resume',
            extracted_text=large_content,
            user=self.user
        )
        
        client = APIClient()
        client.force_authenticate(user=self.user)
        
        with patch('analysis.services.OpenRouterService.generate_cover_letter') as mock_service:
            mock_service.return_value = {
                'success': True,
                'cover_letter': 'Large content handled',
                'prompt_used': 'Large prompt',
                'metadata': {
                    'model': 'large-model',
                    'tokens_used': 800,
                    'processing_time': 3.0,
                    'template_type': 'professional'
                }
            }
            
            response = client.post('/analysis/generate-cover-letter/', {
                'job_id': self.job.id,
                'resume_id': large_resume.id
            })
        
        # Should handle large content without issues
        self.assertEqual(response.status_code, 201)
        
        # Verify service was called with large content
        mock_service.assert_called_once()
        call_kwargs = mock_service.call_args[1]
        self.assertEqual(len(call_kwargs['resume_content']), len(large_content))