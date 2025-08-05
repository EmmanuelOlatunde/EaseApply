from django.test import TestCase
from rest_framework.test import APIRequestFactory

from analysis.serializers import CoverLetterGenerateSerializer, CoverLetterResponseSerializer
from .test_base import BaseAnalysisTestCase, TestDataFactory


class CoverLetterGenerateSerializerTest(BaseAnalysisTestCase):
    """Test suite for CoverLetterGenerateSerializer."""
    
    def setUp(self):
        super().setUp()
        self.factory = APIRequestFactory()
        self.request = self.factory.post('/')
        self.request.user = self.user
    
    def get_serializer(self, data=None, partial=False):
        """Helper method to create serializer with request context."""
        if data is None:
            data = {}
        
        return CoverLetterGenerateSerializer(
            data=data,
            context={'request': self.request},
            partial=partial
        )
    
    def test_valid_serializer_with_both_ids(self):
        """Test serializer validation with valid job_id and resume_id."""
        data = {
            'job_id': self.job_description.id,
            'resume_id': self.resume.id
        }
        
        serializer = self.get_serializer(data=data)
        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.validated_data['job_id'], self.job_description.id)
        self.assertEqual(serializer.validated_data['resume_id'], self.resume.id)
    
    def test_valid_serializer_with_no_ids(self):
        """Test serializer validation with no IDs provided (should use latest)."""
        data = {}
        
        serializer = self.get_serializer(data=data, partial=True)
        self.assertTrue(serializer.is_valid())
        self.assertIsNone(serializer.validated_data.get('job_id'))
        self.assertIsNone(serializer.validated_data.get('resume_id'))
    
    def test_valid_serializer_with_only_job_id(self):
        """Test serializer validation with only job_id provided."""
        data = {'job_id': self.job_description.id}
        
        serializer = self.get_serializer(data=data, partial=True)
        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.validated_data['job_id'], self.job_description.id)
        self.assertIsNone(serializer.validated_data.get('resume_id'))
    
    def test_valid_serializer_with_only_resume_id(self):
        """Test serializer validation with only resume_id provided."""
        data = {'resume_id': self.resume.id}
        
        serializer = self.get_serializer(data=data, partial=True)
        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.validated_data['resume_id'], self.resume.id)
        self.assertIsNone(serializer.validated_data.get('job_id'))
    
    def test_invalid_job_id_nonexistent(self):
        """Test serializer validation with non-existent job_id."""
        data = {'job_id': 99999}
        
        serializer = self.get_serializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('job_id', serializer.errors)
        self.assertIn("not found or you don't have permission", str(serializer.errors['job_id'][0]))
    
    def test_invalid_resume_id_nonexistent(self):
        """Test serializer validation with non-existent resume_id."""
        data = {'resume_id': 99999}
        
        serializer = self.get_serializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('resume_id', serializer.errors)
        self.assertIn("not found or you don't have permission", str(serializer.errors['resume_id'][0]))
    
    def test_invalid_job_id_wrong_user(self):
        """Test serializer validation with job_id belonging to different user."""
        other_job = self.create_job_description(user=self.other_user)
        data = {'job_id': other_job.id}
        
        serializer = self.get_serializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('job_id', serializer.errors)
        self.assertIn("not found or you don't have permission", str(serializer.errors['job_id'][0]))
    
    def test_invalid_resume_id_wrong_user(self):
        """Test serializer validation with resume_id belonging to different user."""
        other_resume = self.create_resume(user=self.other_user)
        data = {'resume_id': other_resume.id}
        
        serializer = self.get_serializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('resume_id', serializer.errors)
        self.assertIn("not found or you don't have permission", str(serializer.errors['resume_id'][0]))
    
    def test_invalid_job_id_negative(self):
        """Test serializer validation with negative job_id."""
        data = {'job_id': -1}
        
        serializer = self.get_serializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('job_id', serializer.errors)
    
    def test_invalid_job_id_zero(self):
        """Test serializer validation with zero job_id."""
        data = {'job_id': 0}
        
        serializer = self.get_serializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('job_id', serializer.errors)
    
    def test_invalid_resume_id_negative(self):
        """Test serializer validation with negative resume_id."""
        data = {'resume_id': -1}
        
        serializer = self.get_serializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('resume_id', serializer.errors)
    
    def test_null_values_allowed(self):
        """Test that null values are allowed for both fields."""
        data = {
            'job_id': None,
            'resume_id': None
        }
        
        serializer = self.get_serializer(data=data, partial=True)
        self.assertTrue(serializer.is_valid())
        self.assertIsNone(serializer.validated_data.get('job_id'))
        self.assertIsNone(serializer.validated_data.get('resume_id'))
    
    def test_cross_field_validation_with_empty_resume_text(self):
        """Test cross-field validation when resume has empty extracted_text."""
        empty_resume = TestDataFactory.create_empty_resume(self.user)
        data = {
            'job_id': self.job_description.id,
            'resume_id': empty_resume.id
        }
        
        serializer = self.get_serializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('non_field_errors', serializer.errors)
        self.assertIn('extracted text content', str(serializer.errors['non_field_errors'][0]))
    
    def test_cross_field_validation_with_whitespace_resume_text(self):
        """Test cross-field validation when resume has only whitespace."""
        whitespace_resume = TestDataFactory.create_whitespace_resume(self.user)
        data = {
            'job_id': self.job_description.id,
            'resume_id': whitespace_resume.id
        }
        
        serializer = self.get_serializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('non_field_errors', serializer.errors)
        self.assertIn('extracted text content', str(serializer.errors['non_field_errors'][0]))
    
    def test_cross_field_validation_ownership_mismatch(self):
        """Test cross-field validation when job and resume belong to different users."""
        other_job = self.create_job_description(user=self.other_user)
        
        # This will fail at individual field validation before cross-field validation
        data = {
            'job_id': other_job.id,
            'resume_id': self.resume.id
        }
        
        serializer = self.get_serializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('job_id', serializer.errors)
    
    def test_cross_field_validation_skipped_when_ids_missing(self):
        """Test that cross-field validation is skipped when IDs are not provided."""
        # When only one ID is provided, cross-field validation should be skipped
        data = {'job_id': self.job_description.id}
        
        serializer = self.get_serializer(data=data, partial=True)
        self.assertTrue(serializer.is_valid())
        
        # When no IDs are provided, cross-field validation should be skipped
        data = {}
        
        serializer = self.get_serializer(data=data, partial=True)
        self.assertTrue(serializer.is_valid())
    
    def test_serializer_field_requirements(self):
        """Test field requirement settings."""
        serializer = self.get_serializer()
        
        # Both fields should be optional
        job_id_field = serializer.fields['job_id']
        resume_id_field = serializer.fields['resume_id']
        
        self.assertFalse(job_id_field.required)
        self.assertFalse(resume_id_field.required)
        self.assertTrue(job_id_field.allow_null)
        self.assertTrue(resume_id_field.allow_null)
    
    def test_serializer_help_text(self):
        """Test that help text is properly set on fields."""
        serializer = self.get_serializer()
        
        job_id_help = serializer.fields['job_id'].help_text
        resume_id_help = serializer.fields['resume_id'].help_text
        
        self.assertIn('optional', job_id_help)
        self.assertIn('latest', job_id_help)
        self.assertIn('optional', resume_id_help)
        self.assertIn('latest', resume_id_help)


class CoverLetterResponseSerializerTest(TestCase):
    """Test suite for CoverLetterResponseSerializer."""
    
    def test_valid_complete_response_data(self):
        """Test serializer with complete valid response data."""
        data = {
            'success': True,
            'cover_letter': 'Generated cover letter content',
            'analysis_id': 123,
            'metadata': {
                'job_title': 'Software Engineer',
                'processing_time': 2.5,
                'tokens_used': 500,
                'model_used': 'gpt-4o',
                'created_at': '2024-01-01T10:00:00Z'
            },
            'message': 'Cover letter generated successfully'
        }
        
        serializer = CoverLetterResponseSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.validated_data['success'], True)
        self.assertEqual(serializer.validated_data['cover_letter'], data['cover_letter'])
        self.assertEqual(serializer.validated_data['analysis_id'], 123)
        self.assertEqual(serializer.validated_data['metadata'], data['metadata'])
        self.assertEqual(serializer.validated_data['message'], data['message'])
    
    def test_valid_minimal_response_data(self):
        """Test serializer with minimal valid response data."""
        data = {
            'success': False
        }
        
        serializer = CoverLetterResponseSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.validated_data['success'], False)
    
    def test_success_field_required(self):
        """Test that success field is required."""
        data = {
            'cover_letter': 'Some content',
            'message': 'Some message'
        }
        
        serializer = CoverLetterResponseSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('success', serializer.errors)
    
    def test_empty_cover_letter_allowed(self):
        """Test that empty cover_letter is allowed."""
        data = {
            'success': True,
            'cover_letter': ''
        }
        
        serializer = CoverLetterResponseSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.validated_data['cover_letter'], '')
    
    def test_optional_fields_not_required(self):
        """Test that optional fields are not required."""
        data = {
            'success': True,
            'cover_letter': 'Content'
            # analysis_id, metadata, message are optional
        }
        
        serializer = CoverLetterResponseSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        
        # Optional fields should not be in validated_data if not provided
        self.assertNotIn('analysis_id', serializer.validated_data)
        self.assertNotIn('metadata', serializer.validated_data)
        self.assertNotIn('message', serializer.validated_data)
    
    def test_metadata_dict_field(self):
        """Test that metadata accepts dictionary data."""
        complex_metadata = {
            'job_title': 'Senior Software Engineer',
            'processing_time': 3.14,
            'tokens_used': 750,
            'model_used': 'gpt-4o-mini',
            'created_at': '2024-01-01T10:00:00Z',
            'additional_info': {
                'nested': 'data',
                'numbers': [1, 2, 3],
                'boolean': True
            }
        }
        
        data = {
            'success': True,
            'cover_letter': 'Content',
            'metadata': complex_metadata
        }
        
        serializer = CoverLetterResponseSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.validated_data['metadata'], complex_metadata)


    def test_invalid_success_field_type(self):
        """Test that success field must be boolean."""
        data = {
            'success': 'not_a_boolean'  # this will cause validation to fail
        }

        serializer = CoverLetterResponseSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('success', serializer.errors)


    def test_invalid_analysis_id_type(self):
        """Test that analysis_id must be integer."""
        data = {
            'success': True,
            'analysis_id': 'not_an_integer'
        }
        
        serializer = CoverLetterResponseSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('analysis_id', serializer.errors)
    
    def test_invalid_metadata_type(self):
        """Test that metadata must be a dictionary."""
        data = {
            'success': True,
            'metadata': 'not_a_dict'
        }
        
        serializer = CoverLetterResponseSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('metadata', serializer.errors)
    
    def test_serialization_output(self):
        """Test serializer output format."""
        data = {
            'success': True,
            'cover_letter': 'Generated cover letter',
            'analysis_id': 456,
            'metadata': {'model': 'test'},
            'message': 'Success'
        }
        
        serializer = CoverLetterResponseSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        
        # Test that serialized data maintains structure
        serialized = serializer.data
        self.assertEqual(serialized['success'], True)
        self.assertEqual(serialized['cover_letter'], 'Generated cover letter')
        self.assertEqual(serialized['analysis_id'], 456)
        self.assertEqual(serialized['metadata'], {'model': 'test'})
        self.assertEqual(serialized['message'], 'Success')
    
    def test_error_response_structure(self):
        """Test serializer with error response structure."""
        data = {
            'success': False,
            'cover_letter': '',
            'message': 'Error occurred during generation'
        }
        
        serializer = CoverLetterResponseSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.validated_data['success'], False)
        self.assertEqual(serializer.validated_data['message'], 'Error occurred during generation')


class SerializerEdgeCasesTest(BaseAnalysisTestCase):
    """Test edge cases and boundary conditions for serializers."""
    
    def setUp(self):
        super().setUp()
        self.factory = APIRequestFactory()
        self.request = self.factory.post('/')
        self.request.user = self.user
    
    def test_generate_serializer_with_string_ids(self):
        """Test serializer with string IDs (should be converted to int)."""
        data = {
            'job_id': str(self.job_description.id),
            'resume_id': str(self.resume.id)
        }
        
        serializer = CoverLetterGenerateSerializer(
            data=data,
            context={'request': self.request}
        )
        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.validated_data['job_id'], self.job_description.id)
        self.assertEqual(serializer.validated_data['resume_id'], self.resume.id)
    
    def test_generate_serializer_with_extra_fields(self):
        """Test serializer ignores extra fields."""
        data = {
            'job_id': self.job_description.id,
            'resume_id': self.resume.id,
            'extra_field': 'should_be_ignored',
            'another_extra': 123
        }
        
        serializer = CoverLetterGenerateSerializer(
            data=data,
            context={'request': self.request}
        )
        self.assertTrue(serializer.is_valid())
        
        # Extra fields should not be in validated_data
        self.assertNotIn('extra_field', serializer.validated_data)
        self.assertNotIn('another_extra', serializer.validated_data)
    
    def test_response_serializer_with_none_values(self):
        """Test response serializer with None values for optional fields."""
        data = {
            'success': True,
            'cover_letter': 'Content',
            'analysis_id': None,
            'metadata': None,
            'message': None
        }
        
        serializer = CoverLetterResponseSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        
        # None values should be preserved
        self.assertIsNone(serializer.validated_data['analysis_id'])
        self.assertIsNone(serializer.validated_data['metadata'])
        self.assertIsNone(serializer.validated_data['message'])
    

    def test_generate_serializer_context_required(self):
        """Test that serializer requires request context for validation."""
        data = {
            'job_id': self.job_description.id,
            'resume_id': self.resume.id
        }

        serializer = CoverLetterGenerateSerializer(data=data)

        with self.assertRaises(KeyError):  # Not AttributeError
            serializer.is_valid()


    def test_very_large_ids(self):
        """Test serializer with very large ID values."""
        import sys
        
        data = {
            'job_id': sys.maxsize,
            'resume_id': sys.maxsize
        }
        
        serializer = CoverLetterGenerateSerializer(
            data=data,
            context={'request': self.request}
        )
        
        # Should fail validation because IDs don't exist
        self.assertFalse(serializer.is_valid())
        self.assertIn('job_id', serializer.errors)
        self.assertIn('resume_id', serializer.errors)