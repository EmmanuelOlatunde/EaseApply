"""
Test suite for Analysis app models.
Tests model creation, validation, relationships, and methods.
"""

from django.contrib.auth import get_user_model
from django.db import IntegrityError
from django.core.exceptions import ValidationError


from analysis.models import AnalysisResult
from .test_base import BaseAnalysisTestCase

User = get_user_model()


class AnalysisResultModelTest(BaseAnalysisTestCase):
    """Test suite for AnalysisResult model."""
    
    def create_analysis_result(self, user=None, job_description=None, resume=None, analysis_type='cover_letter', **kwargs):
        """Helper method to create AnalysisResult for testing."""
        defaults = {
            'user': user or self.user,
            'job_description': job_description or self.job_description,
            'resume': resume or self.resume,
            'analysis_type': analysis_type,
            'prompt_used': 'Test prompt',
            'result_text': 'Generated cover letter content',
            'model_used': 'gpt-4o',
            'tokens_used': 500,
            'processing_time': 2.5
        }
        defaults.update(kwargs)
        return AnalysisResult.objects.create(**defaults)
    
    def test_create_analysis_result_success(self):
        """Test successful creation of AnalysisResult."""
        analysis = self.create_analysis_result()
        
        self.assertEqual(analysis.user, self.user)
        self.assertEqual(analysis.job_description, self.job_description)
        self.assertEqual(analysis.resume, self.resume)
        self.assertEqual(analysis.analysis_type, 'cover_letter')
        self.assertEqual(analysis.prompt_used, 'Test prompt')
        self.assertEqual(analysis.result_text, 'Generated cover letter content')
        self.assertEqual(analysis.model_used, 'gpt-4o')
        self.assertEqual(analysis.tokens_used, 500)
        self.assertEqual(analysis.processing_time, 2.5)
        
        # Check auto-generated fields
        self.assertIsNotNone(analysis.created_at)
        self.assertIsNotNone(analysis.updated_at)
        self.assertIsNotNone(analysis.id)
    
    def test_analysis_result_str_method(self):
        """Test the __str__ method of AnalysisResult."""
        analysis = self.create_analysis_result()
        expected_str = f"{self.user.username} - cover_letter - {analysis.created_at.strftime('%Y-%m-%d')}"
        self.assertEqual(str(analysis), expected_str)
    
    def test_analysis_result_ordering(self):
        """Test that AnalysisResult objects are ordered by creation date descending."""
        # Create multiple analysis results
        analysis1 = self.create_analysis_result()
        analysis2 = self.create_analysis_result()
        analysis3 = self.create_analysis_result()
        
        # Get all results - should be ordered by created_at descending
        results = AnalysisResult.objects.all()
        
        self.assertEqual(results[0], analysis3)  # Most recent first
        self.assertEqual(results[1], analysis2)
        self.assertEqual(results[2], analysis1)  # Oldest last
    
    def test_analysis_types_choices(self):
        """Test all available analysis types can be set."""
        analysis_types = ['cover_letter', 'resume_analysis', 'job_match']
        
        for analysis_type in analysis_types:
            analysis = self.create_analysis_result(analysis_type=analysis_type)
            self.assertEqual(analysis.analysis_type, analysis_type)
    
    def test_nullable_fields(self):
        """Test that nullable fields can be None."""
        analysis = AnalysisResult.objects.create(
            user=self.user,
            analysis_type='cover_letter',
            prompt_used='Test prompt',
            result_text='Test result',
            # job_description and resume are nullable
            job_description=None,
            resume=None,
            # These metadata fields are nullable
            tokens_used=None,
            processing_time=None
        )
        
        self.assertIsNone(analysis.job_description)
        self.assertIsNone(analysis.resume)
        self.assertIsNone(analysis.tokens_used)
        self.assertIsNone(analysis.processing_time)
    
    def test_required_fields(self):
        """Test that required fields cannot be None."""
        with self.assertRaises(IntegrityError):
            AnalysisResult.objects.create(
                # Missing required user field
                analysis_type='cover_letter',
                prompt_used='Test prompt',
                result_text='Test result'
            )
    
    def test_foreign_key_relationships(self):
        """Test foreign key relationships work correctly."""
        analysis = self.create_analysis_result()
        
        # Test user relationship
        self.assertEqual(analysis.user.username, 'testuser')
        self.assertIn(analysis, self.user.analysis_results.all())
        
        # Test job_description relationship
        self.assertEqual(analysis.job_description.title, 'Software Developer')
        
        # Test resume relationship
        self.assertEqual(analysis.resume.full_name, 'John Doe')
    
    def test_cascade_deletion_user(self):
        """Test that deleting user cascades to analysis results."""
        analysis = self.create_analysis_result()
        analysis_id = analysis.id
        
        # Delete the user
        self.user.delete()
        
        # Analysis result should be deleted
        self.assertFalse(AnalysisResult.objects.filter(id=analysis_id).exists())
    
    def test_cascade_deletion_job_description(self):
        """Test that deleting job description cascades to analysis results."""
        analysis = self.create_analysis_result()
        analysis_id = analysis.id
        
        # Delete the job description
        self.job_description.delete()
        
        # Analysis result should be deleted
        self.assertFalse(AnalysisResult.objects.filter(id=analysis_id).exists())
    
    def test_cascade_deletion_resume(self):
        """Test that deleting resume cascades to analysis results."""
        analysis = self.create_analysis_result()
        analysis_id = analysis.id
        
        # Delete the resume
        self.resume.delete()
        
        # Analysis result should be deleted
        self.assertFalse(AnalysisResult.objects.filter(id=analysis_id).exists())
    
    def test_default_values(self):
        """Test model default values."""
        analysis = AnalysisResult.objects.create(
            user=self.user,
            prompt_used='Test prompt',
            result_text='Test result'
            # analysis_type should default to 'cover_letter'
            # model_used should default to 'gpt-4o'
        )
        
        self.assertEqual(analysis.analysis_type, 'cover_letter')
        self.assertEqual(analysis.model_used, 'gpt-4o')
    
    def test_model_indexes(self):
        """Test that database indexes are created correctly."""
        # This tests the Meta indexes configuration
        # Create some test data to ensure indexes work
        user2 = User.objects.create_user(username='user2', email='user2@example.com')
        
        # Create analysis results with different types and users
        self.create_analysis_result(analysis_type='cover_letter')
        self.create_analysis_result(analysis_type='resume_analysis')
        self.create_analysis_result(user=user2, analysis_type='cover_letter')
        
        # These queries should use the indexes
        cover_letter_results = AnalysisResult.objects.filter(
            user=self.user, 
            analysis_type='cover_letter'
        )
        self.assertEqual(cover_letter_results.count(), 1)
        
        recent_results = AnalysisResult.objects.order_by('-created_at')
        self.assertEqual(recent_results.count(), 3)
    
    def test_help_text_fields(self):
        """Test that help text is properly set on fields."""
        field_help_texts = {
            'prompt_used': 'The prompt sent to AI model',
            'result_text': 'Generated content from AI',
            'processing_time': 'Time in seconds'
        }
        
        for field_name, expected_help_text in field_help_texts.items():
            field = AnalysisResult._meta.get_field(field_name)
            self.assertEqual(field.help_text, expected_help_text)
    
    def test_max_length_constraints(self):
        """Test field max length constraints."""
        # Test analysis_type max length
        long_analysis_type = 'x' * 21  # Exceeds max_length=20
        
        analysis = AnalysisResult(
            user=self.user,
            analysis_type=long_analysis_type,
            prompt_used='Test prompt',
            result_text='Test result'
        )
        
        with self.assertRaises(ValidationError):
            analysis.full_clean()
        
        # Test model_used max length
        long_model_name = 'x' * 51  # Exceeds max_length=50
        
        analysis = AnalysisResult(
            user=self.user,
            analysis_type='cover_letter',
            model_used=long_model_name,
            prompt_used='Test prompt',
            result_text='Test result'
        )
        
        with self.assertRaises(ValidationError):
            analysis.full_clean()
    
    def test_multiple_analysis_results_per_user(self):
        """Test that users can have multiple analysis results."""
        # Create multiple analysis results for the same user
        analyses = []
        for i in range(5):
            analysis = self.create_analysis_result(
                analysis_type='cover_letter',
                result_text=f'Cover letter {i+1}'
            )
            analyses.append(analysis)
        
        # Verify all belong to the same user
        user_analyses = self.user.analysis_results.all()
        self.assertEqual(user_analyses.count(), 5)
        
        for analysis in analyses:
            self.assertIn(analysis, user_analyses)
    
    def test_analysis_result_with_different_job_and_resume_users(self):
        """Test analysis result with job and resume from different users."""
        # This tests a potential edge case - normally this shouldn't happen
        # in the application logic, but the model allows it
        other_job = self.create_job_description(user=self.other_user)
        other_resume = self.create_resume(user=self.other_user)
        
        analysis = AnalysisResult.objects.create(
            user=self.user,  # Analysis belongs to user
            job_description=other_job,  # But job belongs to other_user
            resume=other_resume,  # And resume belongs to other_user
            analysis_type='cover_letter',
            prompt_used='Test prompt',
            result_text='Test result'
        )
        
        # Model should allow this (business logic in views should prevent it)
        self.assertEqual(analysis.user, self.user)
        self.assertEqual(analysis.job_description.user, self.other_user)
        self.assertEqual(analysis.resume.user, self.other_user)