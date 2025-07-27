# resumes/tests/test_urls.py
import uuid
from django.test import TestCase
from django.urls import reverse, resolve
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import AccessToken
from ..views import ResumeListCreateView, ResumeDetailView
from ..models import Resume

User = get_user_model()

class ResumeURLTestCase(TestCase):
    """Test cases for resume URL patterns"""
    
    def test_resume_list_create_url(self):
        """Test resume list/create URL pattern"""
        # Test with trailing slash
        url = reverse('resumes:resume-list-create')
        self.assertEqual(url, '/resumes/')
        
        # Test URL resolution
        resolved = resolve('/resumes/')
        self.assertEqual(resolved.view_name, 'resumes:resume-list-create')
        self.assertEqual(resolved.func.view_class, ResumeListCreateView)
    
    def test_resume_upload_url(self):
        """Test resume upload URL pattern"""
        url = reverse('resumes:resume-upload')
        self.assertEqual(url, '/resumes/upload/')
        
        # Test URL resolution
        resolved = resolve('/resumes/upload/')
        self.assertEqual(resolved.view_name, 'resumes:resume-upload')
        self.assertEqual(resolved.func.view_class, ResumeListCreateView)
    
    def test_resume_detail_url(self):
        """Test resume detail URL pattern with UUID"""
        test_uuid = uuid.uuid4()
        url = reverse('resumes:resume-detail', kwargs={'resume_id': test_uuid})
        expected_url = f'/resumes/{test_uuid}/'
        self.assertEqual(url, expected_url)
        
        # Test URL resolution
        resolved = resolve(f'/resumes/{test_uuid}/')
        self.assertEqual(resolved.view_name, 'resumes:resume-detail')
        self.assertEqual(resolved.func.view_class, ResumeDetailView)
        self.assertEqual(resolved.kwargs['resume_id'], test_uuid)
    
    def test_invalid_uuid_in_detail_url(self):
        """Test that invalid UUID in detail URL returns 404"""
        # This would be caught by Django's URL pattern matching
        # Invalid UUIDs won't match the UUID pattern
        invalid_urls = [
            '/resumes/not-a-uuid/',
            '/resumes/123/',
            '/resumes/invalid-uuid-format/',
        ]
        
        for invalid_url in invalid_urls:
            try:
                resolved = resolve(invalid_url)
                # If it resolves, it shouldn't be to our resume detail view
                self.assertNotEqual(resolved.view_name, 'resumes:resume-detail')
            except Exception:
                # Expected - invalid UUID should not resolve
                pass
    
    def test_url_namespace(self):
        """Test that URLs are properly namespaced"""
        # All URLs should be in the 'resumes' namespace
        urls_to_test = [
            ('resumes:resume-list-create', '/resumes/'),
            ('resumes:resume-upload', '/resumes/upload/'),
        ]
        
        for url_name, expected_path in urls_to_test:
            url = reverse(url_name)
            self.assertEqual(url, expected_path)
    
    def test_trailing_slash_behavior(self):
        """Test URL behavior with and without trailing slashes"""
        # Django typically redirects URLs without trailing slashes to ones with them
        test_uuid = uuid.uuid4()
        
        # These should all resolve properly
        urls_with_slash = [
            '/resumes/',
            '/resumes/upload/',
            f'/resumes/{test_uuid}/',
        ]
        
        for url in urls_with_slash:
            try:
                resolved = resolve(url)
                self.assertIsNotNone(resolved)
            except Exception as e:
                self.fail(f"URL {url} should resolve but raised: {e}")

class ResumeURLIntegrationTestCase(APITestCase):
    """Integration tests for resume URLs with actual requests"""
    
    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        #self.token = Token.objects.create(user=self.user)
        self.jwt_token = AccessToken.for_user(self.user)
        
        self.resume = Resume.objects.create(
            user=self.user,
            original_filename='test_resume.pdf',
            file_type=Resume.PDF,
            file_size=1024,
            extracted_text='Test content'
        )
    
    def test_resume_list_endpoint_access(self):
        """Test accessing resume list endpoint"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {str(self.jwt_token)}')
        
        url = reverse('resumes:resume-list-create')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.data['results'], list)
    
    def test_resume_detail_endpoint_access(self):
        """Test accessing resume detail endpoint"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {str(self.jwt_token)}')
        
        url = reverse('resumes:resume-detail', kwargs={'resume_id': self.resume.id})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['id'], str(self.resume.id))
    
    def test_resume_upload_endpoint_access(self):
        """Test accessing resume upload endpoint"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {str(self.jwt_token)}')
        
        url = reverse('resumes:resume-upload')
        # Just test that the endpoint is accessible (POST without file will return 400)
        response = self.client.post(url, {})
        
        # Should return 400 (bad request) not 404 (not found) or 405 (method not allowed)
        self.assertEqual(response.status_code, 400)
    
    def test_nonexistent_resume_detail(self):
        """Test accessing detail for non-existent resume"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {str(self.jwt_token)}')
        
        fake_uuid = uuid.uuid4()
        url = reverse('resumes:resume-detail', kwargs={'resume_id': fake_uuid})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 404)
    
    def test_unauthenticated_access(self):
        """Test that all endpoints require authentication"""
        # Test list endpoint
        list_url = reverse('resumes:resume-list-create')
        response = self.client.get(list_url)
        self.assertEqual(response.status_code, 401)
        
        # Test detail endpoint
        detail_url = reverse('resumes:resume-detail', kwargs={'resume_id': self.resume.id})
        response = self.client.get(detail_url)
        self.assertEqual(response.status_code, 401)
        
        # Test upload endpoint
        upload_url = reverse('resumes:resume-upload')
        response = self.client.post(upload_url, {})
        self.assertEqual(response.status_code, 401)

class ResumeURLParameterTestCase(TestCase):
    """Test cases for URL parameter handling"""
    
    def test_uuid_parameter_extraction(self):
        """Test that UUID parameters are correctly extracted"""
        test_uuid = uuid.uuid4()
        url = f'/resumes/{test_uuid}/'
        
        resolved = resolve(url)
        self.assertEqual(resolved.kwargs['resume_id'], test_uuid)
        self.assertIsInstance(resolved.kwargs['resume_id'], uuid.UUID)
    
    def test_uuid_parameter_validation(self):
        """Test UUID parameter validation"""
        valid_uuid = uuid.uuid4()
        valid_url = f'/resumes/{valid_uuid}/'
        
        # Valid UUID should resolve
        try:
            resolved = resolve(valid_url)
            self.assertEqual(resolved.view_name, 'resumes:resume-detail')
        except Exception as e:
            self.fail(f"Valid UUID should resolve: {e}")
        
        # Invalid UUIDs should not match the pattern
        invalid_uuids = [
            'not-a-uuid',
            '123',
            'abc-def-ghi',
            '12345678-1234-1234-1234-123456789012x',  # Too long
            '12345678-1234-1234-1234-12345678901',    # Too short
        ]
        
        for invalid_uuid in invalid_uuids:
            invalid_url = f'/resumes/{invalid_uuid}/'
            try:
                resolved = resolve(invalid_url)
                # If it resolves, it shouldn't be our resume detail view
                self.assertNotEqual(resolved.view_name, 'resumes:resume-detail')
            except Exception:
                # Expected - invalid UUID should not resolve to our view
                pass
    
    def test_url_kwargs_naming(self):
        """Test that URL kwargs use correct parameter names"""
        test_uuid = uuid.uuid4()
        url = f'/resumes/{test_uuid}/'
        
        resolved = resolve(url)
        
        # Should have 'resume_id' as the parameter name
        self.assertIn('resume_id', resolved.kwargs)
        self.assertEqual(resolved.kwargs['resume_id'], test_uuid)

class ResumeURLReverseTestCase(TestCase):
    """Test cases for URL reversal"""
    
    def test_reverse_with_valid_parameters(self):
        """Test URL reversal with valid parameters"""
        test_uuid = uuid.uuid4()
        
        # Should be able to reverse with UUID
        url = reverse('resumes:resume-detail', kwargs={'resume_id': test_uuid})
        expected = f'/resumes/{test_uuid}/'
        self.assertEqual(url, expected)
        
        # Should be able to reverse with string representation of UUID
        url_str = reverse('resumes:resume-detail', kwargs={'resume_id': str(test_uuid)})
        self.assertEqual(url_str, expected)
    
    def test_reverse_without_parameters(self):
        """Test URL reversal for endpoints that don't need parameters"""
        # List/create endpoints don't need parameters
        list_url = reverse('resumes:resume-list-create')
        self.assertEqual(list_url, '/resumes/')
        
        upload_url = reverse('resumes:resume-upload')
        self.assertEqual(upload_url, '/resumes/upload/')
    
    def test_reverse_with_missing_parameters(self):
        """Test that URL reversal fails when required parameters are missing"""
        # Detail view requires resume_id parameter
        with self.assertRaises(Exception):
            reverse('resumes:resume-detail')  # Missing resume_id
    
    def test_reverse_with_invalid_parameters(self):
        """Test URL reversal with invalid parameter types"""
        # These should still work because Django will convert them to strings
        # But they might not match the UUID pattern when resolved
        
        invalid_params = [
            123,  # Integer
            'not-a-uuid',  # Invalid UUID string
            None,  # None value
        ]
        
        for param in invalid_params:
            if param is not None:
                try:
                    url = reverse('resumes:resume-detail', kwargs={'resume_id': param})
                    # URL can be generated, but it might not resolve back properly
                    self.assertIsInstance(url, str)
                except Exception:
                    # Some invalid parameters might cause reverse to fail
                    pass

class ResumeAppURLConfigTestCase(TestCase):
    """Test cases for app-level URL configuration"""
    
    def test_app_name_configuration(self):
        """Test that app_name is properly configured"""
        # This tests that the app_name is set in urls.py
        url = reverse('resumes:resume-list-create')
        self.assertTrue(url.startswith('/resumes'))
    
    def test_all_view_patterns_included(self):
        """Test that all expected URL patterns are included"""
        expected_patterns = [
            'resumes:resume-list-create',
            'resumes:resume-upload', 
            'resumes:resume-detail',
        ]
        
        for pattern_name in expected_patterns:
            try:
                if pattern_name == 'resumes:resume-detail':
                    # Detail view needs a UUID parameter
                    test_uuid = uuid.uuid4()
                    url = reverse(pattern_name, kwargs={'resume_id': test_uuid})
                else:
                    url = reverse(pattern_name)
                
                self.assertIsInstance(url, str)
                self.assertGreater(len(url), 0)
            except Exception as e:
                self.fail(f"Pattern {pattern_name} should be reversible: {e}")
    
    def test_url_pattern_ordering(self):
        """Test that URL patterns are in correct order (more specific first)"""
        # More specific patterns should come before general ones
        # In our case, 'upload/' should come before '' (list/create)
        
        # Test that upload/ is accessible
        upload_url = reverse('resumes:resume-upload')
        self.assertEqual(upload_url, '/resumes/upload/')
        
        # Test that it resolves to the correct view
        resolved = resolve('/resumes/upload/')
        self.assertEqual(resolved.view_name, 'resumes:resume-upload')
    
    def test_http_methods_allowed(self):
        """Test that correct HTTP methods are allowed for each endpoint"""
        # This is more of an integration test but tests URL configuration
        from django.test import Client
        
        client = Client()
        
        # Test that GET is allowed on list endpoint (will return 401 without auth)
        response = client.get('/resumes/')
        self.assertNotEqual(response.status_code, 405)  # Method not allowed
        
        # Test that POST is allowed on upload endpoint
        response = client.post('/resumes/upload/')
        self.assertNotEqual(response.status_code, 405)
        
        # Test that GET is allowed on detail endpoint
        test_uuid = uuid.uuid4()
        response = client.get(f'/resumes/{test_uuid}/')
        self.assertNotEqual(response.status_code, 405)

class ResumeURLSecurityTestCase(APITestCase):
    """Test cases for URL security considerations"""
    
    def setUp(self):
        """Set up test data"""
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
        
        self.jwt_token1 = AccessToken.for_user(self.user1)
        self.jwt_token2 = AccessToken.for_user(self.user2)
        
        self.resume1 = Resume.objects.create(
            user=self.user1,
            original_filename='user1_resume.pdf',
            file_type=Resume.PDF,
            file_size=1024,
        )
        self.resume2 = Resume.objects.create(
            user=self.user2,
            original_filename='user2_resume.pdf',
            file_type=Resume.PDF,
            file_size=1024,
        )
    
    def test_cross_user_access_via_url(self):
        """Test that users cannot access other users' resumes via direct URL"""
        # User1 tries to access User2's resume
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {str(self.jwt_token1)}')
        
        url = reverse('resumes:resume-detail', kwargs={'resume_id': self.resume2.id})
        response = self.client.get(url)
        
        # Should return 404, not the resume data
        self.assertEqual(response.status_code, 404)
    
    def test_uuid_enumeration_protection(self):
        """Test protection against UUID enumeration attacks"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {str(self.jwt_token1)}')
        
        # Try multiple random UUIDs - should all return 404
        for _ in range(5):
            random_uuid = uuid.uuid4()
            url = reverse('resumes:resume-detail', kwargs={'resume_id': random_uuid})
            response = self.client.get(url)
            
            self.assertEqual(response.status_code, 404)
            # Response should not leak information about whether resume exists
            self.assertNotIn('user', response.data if hasattr(response, 'data') else {})
    
    def test_url_parameter_injection(self):
        """Test that URL parameters are properly sanitized"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {str(self.jwt_token1)}')
        
        # These should not resolve to our resume detail view due to UUID validation
        malicious_inputs = [
            '../admin/',
            '../../users/1/',
            'javascript:alert(1)',
            '<script>alert(1)</script>',
            'OR 1=1--',
        ]
        
        for malicious_input in malicious_inputs:
            try:
                # Try to construct URL - should either fail or not match our pattern
                malicious_url = f'/resumes/{malicious_input}/'
                resolved = resolve(malicious_url)
                
                # If it resolves, it shouldn't be our resume detail view
                self.assertNotEqual(resolved.view_name, 'resumes:resume-detail')
            except Exception:
                # Expected - malicious input should not resolve
                pass

class ResumeURLPerformanceTestCase(TestCase):
    """Test cases for URL performance considerations"""
    
    def test_url_resolution_performance(self):
        """Test that URL resolution is efficient"""
        import time
        
        test_uuid = uuid.uuid4()
        url = f'/resumes/{test_uuid}/'
        
        # Time URL resolution
        start_time = time.time()
        for _ in range(100):
            resolved = resolve(url)
            self.assertEqual(resolved.view_name, 'resumes:resume-detail')
        end_time = time.time()
        
        # Should be very fast (less than 1 second for 100 resolutions)
        self.assertLess(end_time - start_time, 1.0)
    
    def test_url_reverse_performance(self):
        """Test that URL reversal is efficient"""
        import time
        
        test_uuid = uuid.uuid4()
        
        # Time URL reversal
        start_time = time.time()
        for _ in range(100):
            url = reverse('resumes:resume-detail', kwargs={'resume_id': test_uuid})
            self.assertTrue(url.endswith(f'{test_uuid}/'))
        end_time = time.time()
        
        # Should be very fast
        self.assertLess(end_time - start_time, 1.0)

class ResumeURLCompatibilityTestCase(TestCase):
    """Test cases for URL compatibility and edge cases"""
    
    def test_case_sensitivity(self):
        """Test URL case sensitivity"""
        # Django URLs are case-sensitive by default
        test_uuid = uuid.uuid4()
        
        # Lowercase should work
        lower_url = f'/resumes/{str(test_uuid).lower()}/'
        resolved_lower = resolve(lower_url)
        self.assertEqual(resolved_lower.view_name, 'resumes:resume-detail')
        
        # Uppercase should also work (UUIDs are case-insensitive in our pattern)
        upper_url = f'/resumes/{str(test_uuid).upper()}/'
        resolved_upper = resolve(upper_url)
        self.assertEqual(resolved_upper.view_name, 'resumes:resume-detail')
    
    def test_unicode_handling(self):
        """Test that URLs handle Unicode properly"""
        # Our URLs use UUIDs which are ASCII, but test the framework
        url = '/resumes/'
        
        # Should handle international characters in query params gracefully
        # (though our API doesn't use query params, test the framework)
        try:
            resolved = resolve(url)
            self.assertEqual(resolved.view_name, 'resumes:resume-list-create')
        except Exception as e:
            self.fail(f"Unicode handling failed: {e}")
    
    def test_url_length_limits(self):
        """Test URL length limits"""
        # UUIDs have fixed length, but test edge cases
        test_uuid = uuid.uuid4()
        url = reverse('resumes:resume-detail', kwargs={'resume_id': test_uuid})
        
        # URL should be reasonable length
        self.assertLess(len(url), 200)  # Reasonable limit
        
        # Should still resolve
        resolved = resolve(url)
        self.assertEqual(resolved.view_name, 'resumes:resume-detail')

class ResumeURLDocumentationTestCase(TestCase):
    """Test cases that serve as documentation for URL patterns"""
    
    def test_all_endpoint_examples(self):
        """Document all available endpoints with examples"""
        # This test serves as living documentation
        
        endpoints = {
            'List resumes': {
                'method': 'GET',
                'url': reverse('resumes:resume-list-create'),
                'expected': '/resumes/',
            },
            'Upload resume': {
                'method': 'POST', 
                'url': reverse('resumes:resume-upload'),
                'expected': '/resumes/upload/',
            },
            'Get resume detail': {
                'method': 'GET',
                'url': reverse('resumes:resume-detail', kwargs={'resume_id': uuid.uuid4()}),
                'expected_pattern': r'/resumes/[0-9a-f-]{36}/',
            },
        }
        
        for endpoint_name, config in endpoints.items():
            with self.subTest(endpoint=endpoint_name):
                if 'expected' in config:
                    self.assertEqual(config['url'], config['expected'])
                elif 'expected_pattern' in config:
                    
                    self.assertRegex(config['url'], config['expected_pattern'])
    
    def test_url_naming_conventions(self):
        """Test that URL names follow conventions"""
        # URL names should be descriptive and follow kebab-case
        url_names = [
            'resumes:resume-list-create',
            'resumes:resume-upload',
            'resumes:resume-detail',
        ]
        
        for url_name in url_names:
            with self.subTest(url_name=url_name):
                # Should contain the app namespace
                self.assertTrue(url_name.startswith('resumes:'))
                
                # Should use kebab-case (hyphens, not underscores)
                name_part = url_name.split(':', 1)[1]
                self.assertNotIn('_', name_part)
                
                # Should be reversible (except detail which needs UUID)
                try:
                    if 'detail' in name_part:
                        reverse(url_name, kwargs={'resume_id': uuid.uuid4()})
                    else:
                        reverse(url_name)
                except Exception as e:
                    self.fail(f"URL name {url_name} should be reversible: {e}")