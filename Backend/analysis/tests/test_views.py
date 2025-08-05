"""
Test suite for Analysis app views.
Comprehensive tests for GenerateCoverLetterView including permissions, 
error handling, edge cases, and business logic.
"""

from rest_framework import status
from unittest.mock import patch
from analysis.models import AnalysisResult
from .test_base import BaseAnalysisTestCase, MockServiceMixin, TestDataFactory
from ..services import OpenRouterService

import time
from django.contrib.auth import get_user_model
from jobs.models import JobDescription


User = get_user_model()

class GenerateCoverLetterViewTest(BaseAnalysisTestCase, MockServiceMixin):
    """Test suite for GenerateCoverLetterView."""

    def test_successful_cover_letter_generation_without_ids(self):
        """Test successful cover letter generation using latest job and resume."""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {str(self.token)}')
        with self.patch_openrouter_service():
            response = self.client.post(self.cover_letter_url, {})
        
        self.assert_successful_response(response, status.HTTP_201_CREATED)
        
        # Verify it used the latest job and resume
        analysis = AnalysisResult.objects.get(user=self.user)
        self.assertEqual(analysis.job_description, self.job_description)
        self.assertEqual(analysis.resume, self.resume)
    
    def test_successful_generation_with_only_job_id(self):
        """Test successful generation with only job_id provided."""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {str(self.token)}')
        # Ensure the resume has content
        latest_resume  =TestDataFactory.create_valid_resume(self.user)

        with self.patch_openrouter_service():
            response = self.client.post(self.cover_letter_url, {
                'job_id': self.job_description.id
            })
        
        self.assert_successful_response(response, status.HTTP_201_CREATED)
        
        # Should use provided job and latest resume
        analysis = AnalysisResult.objects.get(user=self.user)
        self.assertEqual(analysis.job_description, self.job_description)
        self.assertEqual(analysis.resume.id, latest_resume.id)
        



    def test_unauthenticated_access_denied(self):
        """Test that unauthenticated users cannot access the endpoint."""
        self.unauthenticate()
        
        response = self.client.post(self.cover_letter_url, {
            'job_id': self.job_description.id,
            'resume_id': self.resume.id
        })
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_invalid_job_id_not_found(self):
        """Test error when job_id doesn't exist."""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {str(self.token)}')
        response = self.client.post(self.cover_letter_url, {
            'job_id': 99999,
            'resume_id': self.resume.id
        })
        
        self.assert_error_response(response, status.HTTP_400_BAD_REQUEST)
    
    def test_invalid_resume_id_not_found(self):
        """Test error when resume_id doesn't exist."""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {str(self.token)}')
        response = self.client.post(self.cover_letter_url, {
            'job_id': self.job_description.id,
            'resume_id': 99999
        })
        
        self.assert_error_response(response, status.HTTP_400_BAD_REQUEST)
    
    def test_job_belongs_to_different_user(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {str(self.other_token)}')
        """Test error when job belongs to different user."""
        other_job = self.create_job_description(user=self.other_user)
        
        response = self.client.post(self.cover_letter_url, {
            'job_id': other_job.id,
            'resume_id': self.resume.id
        })
        
        self.assert_error_response(response, status.HTTP_400_BAD_REQUEST)
    
    def test_resume_belongs_to_different_user(self):
        """Test error when resume belongs to different user."""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {str(self.other_token)}')
        other_resume = self.create_resume(user=self.other_user)
        
        response = self.client.post(self.cover_letter_url, {
            'job_id': self.job_description.id,
            'resume_id': other_resume.id
        })
        
        self.assert_error_response(response, status.HTTP_400_BAD_REQUEST)

    def test_empty_resume_text_validation(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {str(self.token)}')
        empty_resume = TestDataFactory.create_empty_resume(self.user)
        
        data = {
            'job_id': self.job_description.id,
            'resume_id': empty_resume.id,  # Ensure valid ID
            'template_type': 'professional'
        }
        
        response = self.client.post(self.cover_letter_url, data, format='json')
        
        self.assert_error_response(response, status.HTTP_400_BAD_REQUEST)
        self.assertIn(
            'Resume must have extracted text content for analysis.', 
            str(response.data)
        )


    def test_whitespace_resume_text_validation(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {str(self.token)}')
        whitespace_resume = TestDataFactory.create_whitespace_resume(self.user)

        data = {
            'job_id': self.job_description.id,
            'resume_id': whitespace_resume.id,  # Ensure valid ID
            'template_type': 'professional'
        }

        response = self.client.post(self.cover_letter_url, data, format='json')

        self.assert_error_response(response, status.HTTP_400_BAD_REQUEST)
        self.assertIn(
            'extracted text', 
            str(response.data).lower()
        )


    @patch.object(OpenRouterService, 'generate_cover_letter')
    def test_ai_service_failure(self, mock_generate):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {str(self.token)}')
        mock_generate.return_value = {
            'success': False,
            'error': 'AI service unavailable',
            'error_type': 'service_error'
        }
        
        valid_resume = TestDataFactory.create_valid_resume(self.user)
        
        data = {
            'job_id': self.job_description.id,
            'resume_id': valid_resume.id,
            'template_type': 'professional'
        }
        
        response = self.client.post(self.cover_letter_url, data, format='json')
        
        self.assert_error_response(response, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertIn('AI service unavailable', str(response.data))


    @patch.object(OpenRouterService, 'generate_cover_letter')
    def test_ai_service_exception(self, mock_generate):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {str(self.token)}')
        mock_generate.side_effect = Exception("Unexpected AI service error")
        
        valid_resume = TestDataFactory.create_valid_resume(self.user)
        
        data = {
            'job_id': self.job_description.id,
            'resume_id': valid_resume.id,
            'template_type': 'professional'
        }
        
        response = self.client.post(self.cover_letter_url, data, format='json')
        
        self.assert_error_response(response, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertIn('AI service encountered an error', str(response.data))


    @patch.object(OpenRouterService, 'generate_cover_letter')
    def test_successful_cover_letter_generation_with_ids(self, mock_generate):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {str(self.token)}')
        mock_generate.return_value = {
            'success': True,
            'cover_letter': 'Generated cover letter content',
            'prompt_used': 'Test prompt used',
            'metadata': {
                'model': 'gpt-4o',
                'tokens_used': 500,
                'processing_time': 2.5
            }
        }
        
        valid_resume = TestDataFactory.create_valid_resume(self.user)
        
        data = {
            'job_id': self.job_description.id,
            'resume_id': valid_resume.id,
            'template_type': 'professional'
        }
        
        response = self.client.post(self.cover_letter_url, data, format='json')
        
        self.assert_successful_response(response, status.HTTP_201_CREATED)
        self.assertEqual(response.data['cover_letter'], 'Generated cover letter content')
        self.assertTrue(response.data['success'])

    def test_generation_with_multiple_resumes_uses_latest(self):
        """Test that latest resume is used when no resume_id provided and multiple resumes exist."""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {str(self.token)}')
        # Create multiple resumes
        TestDataFactory.create_valid_resume(
            self.user, 
            extracted_text="Older resume content",
            full_name="Older Resume"
        )
        
        # Wait a moment to ensure different timestamps
        time.sleep(0.01)
        
        newer_resume = TestDataFactory.create_valid_resume(
            self.user,
            extracted_text="Newer resume content", 
            full_name="Newer Resume"
        )
        
        # Mock successful AI service response
        mock_result = {
            'success': True,
            'cover_letter': 'Generated cover letter content',
            'prompt_used': 'Test prompt used',
            'metadata': {
                'model': 'gpt-4o',
                'tokens_used': 500,
                'processing_time': 2.5
            }
        }
        
        with patch.object(OpenRouterService, 'generate_cover_letter', return_value=mock_result):
            data = {
                'job_id': self.job_description.id,
                'template_type': 'professional'
                # No resume_id provided - should use latest
            }
            
            response = self.client.post(self.cover_letter_url, data, format='json')
            
            self.assert_successful_response(response, status.HTTP_201_CREATED)
            
            # Verify the newer resume was used
            analysis = AnalysisResult.objects.get(id=response.data['analysis_id'])
            self.assertEqual(analysis.resume, newer_resume)

    def test_generation_with_multiple_jobs_uses_latest(self):
        """Test that latest job is used when no job_id provided and multiple jobs exist."""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {str(self.token)}')
        # Create multiple jobs using the factory method
        TestDataFactory.create_multiple_jobs(self.user, count=3)
        
        # Get the latest job (should be the last one created)
        latest_job = JobDescription.objects.filter(user=self.user).order_by('-created_at').first()
        
        valid_resume = TestDataFactory.create_valid_resume(self.user)
        
        mock_result = {
            'success': True,
            'cover_letter': 'Generated cover letter content',
            'prompt_used': 'Test prompt used',
            'metadata': {
                'model': 'gpt-4o',
                'tokens_used': 500,
                'processing_time': 2.5
            }
        }
        
        with patch.object(OpenRouterService, 'generate_cover_letter', return_value=mock_result):
            data = {
                'resume_id': valid_resume.id,
                'template_type': 'professional'
                # No job_id provided - should use latest
            }
            
            response = self.client.post(self.cover_letter_url, data, format='json')
            
            self.assert_successful_response(response, status.HTTP_201_CREATED)
            
            # Verify the latest job was used
            analysis = AnalysisResult.objects.get(id=response.data['analysis_id'])
            self.assertEqual(analysis.job_description, latest_job)

    def test_no_jobs_found_for_user(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {str(self.token)}')
        self.job_description.delete()
        
        valid_resume = TestDataFactory.create_valid_resume(self.user)
        
        data = {
            'resume_id': valid_resume.id,
            'template_type': 'professional'
        }
        
        response = self.client.post(self.cover_letter_url, data, format='json')
        
        self.assert_error_response(response, status.HTTP_404_NOT_FOUND)
        self.assertIn('No job descriptions found', str(response.data))


    def test_no_resumes_found_for_user(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {str(self.token)}')
        self.resume.delete()
        
        data = {
            'job_id': self.job_description.id,
            'template_type': 'professional'
        }
        
        response = self.client.post(self.cover_letter_url, data, format='json')
        
        self.assert_error_response(response, status.HTTP_404_NOT_FOUND)
        self.assertIn('No resumes found', str(response.data))


    @patch.object(OpenRouterService, 'generate_cover_letter')
    def test_database_transaction_rollback_on_error(self, mock_generate):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {str(self.token)}')
        mock_generate.return_value = {
            'success': True,
            'cover_letter': 'Generated cover letter content',
            'prompt_used': 'Test prompt used',
            'metadata': {
                'model': 'gpt-4o',
                'tokens_used': 500,
                'processing_time': 2.5
            }
        }
        
        valid_resume = TestDataFactory.create_valid_resume(self.user)
        
        with patch('analysis.models.AnalysisResult.objects.create', side_effect=Exception("Database error")):
            data = {
                'job_id': self.job_description.id,
                'resume_id': valid_resume.id,
                'template_type': 'professional'
            }
            
            response = self.client.post(self.cover_letter_url, data, format='json')
            
            self.assert_error_response(response, status.HTTP_500_INTERNAL_SERVER_ERROR)
            self.assertIn('Database error occurred', str(response.data))



    @patch.object(OpenRouterService, 'generate_cover_letter')
    def test_successful_generation_with_only_resume_id(self, mock_generate):
        """Test successful generation with only resume_id provided."""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {str(self.token)}')
        mock_generate.return_value = {
            'success': True,
            'cover_letter': 'Generated cover letter content',
            'prompt_used': 'Test prompt used',
            'metadata': {
                'model': 'gpt-4o',
                'tokens_used': 500,
                'processing_time': 2.5
            }
        }
        
        valid_resume = TestDataFactory.create_valid_resume(self.user)
        
        data = {
            'resume_id': valid_resume.id,
            'template_type': 'professional'
            # No job_id - should use latest job
        }
        
        response = self.client.post(self.cover_letter_url, data, format='json')
        
        self.assert_successful_response(response, status.HTTP_201_CREATED)
        
        # Verify analysis was created with correct job and resume
        analysis = AnalysisResult.objects.get(id=response.data['analysis_id'])
        self.assertEqual(analysis.resume, valid_resume)
        self.assertEqual(analysis.job_description, self.job_description)

    @patch.object(OpenRouterService, 'generate_cover_letter')
    def test_generation_with_professional_template(self, mock_generate):
        """Test cover letter generation with professional template type."""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {str(self.token)}')
        mock_generate.return_value = {
            'success': True,
            'cover_letter': 'Professional cover letter content',
            'prompt_used': 'Professional template prompt',
            'metadata': {
                'model': 'gpt-4o',
                'tokens_used': 600,
                'processing_time': 3.0
            }
        }
        
        valid_resume = TestDataFactory.create_valid_resume(self.user)
        
        data = {
            'job_id': self.job_description.id,
            'resume_id': valid_resume.id,
            'template_type': 'creative'
        }
        
        response = self.client.post(self.cover_letter_url, data, format='json')
        
        self.assert_successful_response(response, status.HTTP_201_CREATED)
        
        # Verify the AI service was called with creative template
        mock_generate.assert_called_once()
        call_kwargs = mock_generate.call_args[1]
        self.assertEqual(call_kwargs['template_type'], 'professional')

    @patch.object(OpenRouterService, 'generate_cover_letter')
    def test_analysis_result_creation_with_metadata(self, mock_generate):
        """Test that AnalysisResult is created with correct metadata."""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {str(self.token)}')
        mock_generate.return_value = {
            'success': True,
            'cover_letter': 'Test cover letter',
            'prompt_used': 'Test prompt',
            'metadata': {
                'model': 'test-model',
                'tokens_used': 100,
                'processing_time': 1.5
            }
        }
        
        valid_resume = TestDataFactory.create_valid_resume(self.user)
        
        data = {
            'job_id': self.job_description.id,
            'resume_id': valid_resume.id,
            'template_type': 'professional'
        }
        
        response = self.client.post(self.cover_letter_url, data, format='json')
        
        self.assert_successful_response(response, status.HTTP_201_CREATED)
        
        # Verify AnalysisResult was created with correct metadata
        analysis = AnalysisResult.objects.get(id=response.data['analysis_id'])
        self.assertEqual(analysis.user, self.user)
        self.assertEqual(analysis.job_description, self.job_description)
        self.assertEqual(analysis.resume, valid_resume)
        self.assertEqual(analysis.analysis_type, 'cover_letter')
        self.assertEqual(analysis.model_used, 'test-model')
        self.assertEqual(analysis.tokens_used, 100)
        self.assertEqual(analysis.processing_time, 1.5)

    @patch.object(OpenRouterService, 'generate_cover_letter')
    def test_response_serialization_validation(self, mock_generate):
        """Test that response data is validated by response serializer."""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {str(self.token)}')
        mock_generate.return_value = {
            'success': True,
            'cover_letter': 'Test cover letter',
            'prompt_used': 'Test prompt',
            'metadata': {
                'model': 'test-model',
                'tokens_used': 200,
                'processing_time': 2.0
            }
        }
        
        valid_resume = TestDataFactory.create_valid_resume(self.user)
        
        data = {
            'job_id': self.job_description.id,
            'resume_id': valid_resume.id,
            'template_type': 'professional'
        }
        
        response = self.client.post(self.cover_letter_url, data, format='json')
        
        self.assert_successful_response(response, status.HTTP_201_CREATED)
        
        # Verify response structure matches serializer
        required_fields = ['success', 'cover_letter', 'analysis_id', 'metadata', 'message']
        for field in required_fields:
            self.assertIn(field, response.data)

    @patch.object(OpenRouterService, 'generate_cover_letter')
    def test_job_description_not_found_after_validation(self, mock_generate):
        """Test race condition where job is deleted after validation but before generation."""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {str(self.token)}')
        
        def delete_job_during_generation(*args, **kwargs):
            # Delete the job during AI generation to simulate race condition
            JobDescription.objects.get(pk=self.job_description.id).delete()
            return {
                'success': True,
                'cover_letter': 'Test cover letter',
                'prompt_used': 'Test prompt',
                'metadata': {
                    'model': 'test-model',
                    'tokens_used': 100,
                    'processing_time': 1.0
                }
            }
        
        mock_generate.side_effect = delete_job_during_generation
        
        valid_resume = TestDataFactory.create_valid_resume(self.user)
        
        data = {
            'job_id': self.job_description.id,
            'resume_id': valid_resume.id,
            'template_type': 'professional'
        }
        
        response = self.client.post(self.cover_letter_url, data, format='json')
        
        # Assert the correct status code and updated error message
        self.assertEqual(response.status_code, status.HTTP_410_GONE)
        self.assertIn("deleted before the analysis could be saved", response.data["message"])