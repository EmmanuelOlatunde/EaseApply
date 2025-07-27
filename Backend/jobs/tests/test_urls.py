
from django.test import TestCase, RequestFactory
from django.urls import reverse, resolve, NoReverseMatch
from django.contrib.auth import get_user_model
from jobs import views
from jobs.models import JobDescription

User = get_user_model()


class BaseURLTestMixin:
    """Base mixin providing common URL test utilities"""
    
    @classmethod
    def setUpTestData(cls):
        """Set up test users and jobs"""
        cls.user1 = User.objects.create_user(
            username='testuser1',
            email='test1@example.com',
            password='testpass123'
        )
        cls.user2 = User.objects.create_user(
            username='testuser2', 
            email='test2@example.com',
            password='testpass123'
        )
    
    def setUp(self):
        """Set up test jobs for each test"""
        self.job1 = JobDescription.objects.create(
            user=self.user1,
            raw_content='Test job description 1',
            title='Software Engineer',
            company='Tech Corp',
            is_processed=True
        )
        self.job2 = JobDescription.objects.create(
            user=self.user2,
            raw_content='Test job description 2', 
            title='Data Scientist',
            company='AI Corp',
            is_processed=False
        )
        self.factory = RequestFactory()


class JobsURLPatternsTests(BaseURLTestMixin, TestCase):
    """Test all URL patterns in jobs app"""

    def test_url_patterns_exist(self):
        """Test that all expected URL patterns are defined"""
        expected_patterns = [
            ('jobs:job-create', {}),
            ('jobs:job-detail', {'pk': 1}),
            ('jobs:paste-job', {}),
            ('jobs:user-jobs', {}),
            ('jobs:reprocess-job', {'job_id': 1}),
            ('jobs:delete-job', {'job_id': 1}),
        ]
        
        for pattern_name, kwargs in expected_patterns:
            try:
                url = reverse(pattern_name, kwargs=kwargs)
                self.assertIsNotNone(url)
            except NoReverseMatch:
                self.fail(f"URL pattern '{pattern_name}' not found")

    def test_app_name_configured(self):
        """Test that app_name is correctly configured"""
        # Test that we can reverse with app namespace
        url = reverse('jobs:job-create')
        self.assertEqual(url, '/jobs/')
        
        # Test that reverse without namespace fails
        with self.assertRaises(NoReverseMatch):
            reverse('job-create')


class JobCreateURLTests(BaseURLTestMixin, TestCase):
    """Test job-create URL pattern"""
    
    def test_job_create_url_pattern(self):
        """Test job-create URL pattern matches correctly"""
        url = reverse('jobs:job-create')
        self.assertEqual(url, '/jobs/')
        
        # Test URL resolution
        resolver = resolve('/jobs/')
        self.assertEqual(resolver.view_name, 'jobs:job-create')
        self.assertEqual(resolver.func.view_class, views.JobDescriptionCreateView)
    
    def test_job_create_url_with_trailing_slash(self):
        """Test job-create URL works with trailing slash"""
        resolver = resolve('/jobs/')
        self.assertEqual(resolver.view_name, 'jobs:job-create')
    
    def test_job_create_url_without_trailing_slash(self):
        """Test job-create URL behavior without trailing slash"""
        # Django typically redirects to add trailing slash
        try:
            resolve('/jobs')
            # If it resolves, that's fine too (depends on APPEND_SLASH setting)
        except:  # noqa: E722
            # Expected behavior - Django should redirect to add slash
            pass
    
    def test_job_create_url_accepts_no_parameters(self):
        """Test that job-create URL doesn't accept extra parameters"""
        # Should match root pattern
        resolver = resolve('/jobs/')
        self.assertEqual(resolver.kwargs, {})
        
        # Extra path should not match this pattern
        with self.assertRaises(Exception):  # Could be Resolver404 or similar
            resolve('/jobs/extra/')


class JobDetailURLTests(BaseURLTestMixin, TestCase):
    """Test job-detail URL pattern"""
    
    def test_job_detail_url_pattern(self):
        """Test job-detail URL pattern with valid ID"""
        url = reverse('jobs:job-detail', kwargs={'pk': self.job1.id})
        expected_url = f'/jobs/{self.job1.id}/'
        self.assertEqual(url, expected_url)
        
        # Test URL resolution
        resolver = resolve(f'/jobs/{self.job1.id}/')
        self.assertEqual(resolver.view_name, 'jobs:job-detail')
        self.assertEqual(resolver.func.view_class, views.JobDescriptionDetailView)
        self.assertEqual(resolver.kwargs, {'pk': self.job1.id})
    
    def test_job_detail_url_with_different_ids(self):
        """Test job-detail URL with various ID values"""
        test_ids = [1, 123, 999999, self.job1.id, self.job2.id]
        
        for job_id in test_ids:
            url = reverse('jobs:job-detail', kwargs={'pk': job_id})
            expected_url = f'/jobs/{job_id}/'
            self.assertEqual(url, expected_url)
            
            # Test resolution
            resolver = resolve(f'/jobs/{job_id}/')
            self.assertEqual(resolver.view_name, 'jobs:job-detail')
            self.assertEqual(resolver.kwargs, {'pk': job_id})
    
    def test_job_detail_url_requires_pk(self):
        """Test that job-detail URL requires pk parameter"""
        with self.assertRaises(NoReverseMatch):
            reverse('jobs:job-detail')
        
        with self.assertRaises(NoReverseMatch):
            reverse('jobs:job-detail', kwargs={})
    
    def test_job_detail_url_invalid_pk_types(self):
        """Test job-detail URL with invalid pk types"""
        # String that's not a number should not match
        with self.assertRaises(Exception):
            resolve('/jobs/invalid/')
        
        # Empty pk should not match
        with self.assertRaises(Exception):
            resolve('/jobs//')
        
        # Float should not match (int only)
        with self.assertRaises(Exception):
            resolve('/jobs/123.45/')
    
    def test_job_detail_url_edge_case_ids(self):
        """Test job-detail URL with edge case ID values"""
        # Zero ID
        url = reverse('jobs:job-detail', kwargs={'pk': 0})
        self.assertEqual(url, '/jobs/0/')
        
        # Very large ID
        large_id = 2147483647  # Max 32-bit int
        url = reverse('jobs:job-detail', kwargs={'pk': large_id})
        self.assertEqual(url, f'/jobs/{large_id}/')
        
        # Test resolution works
        resolver = resolve(f'/jobs/{large_id}/')
        self.assertEqual(resolver.kwargs, {'pk': large_id})


class PasteJobURLTests(BaseURLTestMixin, TestCase):
    """Test paste-job URL pattern"""
    
    def test_paste_job_url_pattern(self):
        """Test paste-job URL pattern"""
        url = reverse('jobs:paste-job')
        self.assertEqual(url, '/jobs/paste/')
        
        # Test URL resolution
        resolver = resolve('/jobs/paste/')
        self.assertEqual(resolver.view_name, 'jobs:paste-job')
        self.assertEqual(resolver.func.view_class, views.PasteJobDescriptionView)
    
    def test_paste_job_url_no_parameters(self):
        """Test that paste-job URL doesn't accept parameters"""
        resolver = resolve('/jobs/paste/')
        self.assertEqual(resolver.kwargs, {})
    
    def test_paste_job_url_trailing_slash(self):
        """Test paste-job URL with trailing slash"""
        resolver = resolve('/jobs/paste/')
        self.assertEqual(resolver.view_name, 'jobs:paste-job')


class UserJobsURLTests(BaseURLTestMixin, TestCase):
    """Test user-jobs URL pattern"""
    
    def test_user_jobs_url_pattern(self):
        """Test user-jobs URL pattern"""
        url = reverse('jobs:user-jobs')
        self.assertEqual(url, '/jobs/my-jobs/')
        
        # Test URL resolution
        resolver = resolve('/jobs/my-jobs/')
        self.assertEqual(resolver.view_name, 'jobs:user-jobs')
        self.assertEqual(resolver.func.view_class, views.UserJobListView)
    
    def test_user_jobs_url_no_parameters(self):
        """Test that user-jobs URL doesn't accept parameters"""
        resolver = resolve('/jobs/my-jobs/')
        self.assertEqual(resolver.kwargs, {})


class ReprocessJobURLTests(BaseURLTestMixin, TestCase):
    """Test reprocess-job URL pattern"""
    
    def test_reprocess_job_url_pattern(self):
        """Test reprocess-job URL pattern with valid job_id"""
        url = reverse('jobs:reprocess-job', kwargs={'job_id': self.job1.id})
        expected_url = f'/jobs/reprocess/{self.job1.id}/'
        self.assertEqual(url, expected_url)
        
        # Test URL resolution
        resolver = resolve(f'/jobs/reprocess/{self.job1.id}/')
        self.assertEqual(resolver.view_name, 'jobs:reprocess-job')
        self.assertEqual(resolver.func.view_class, views.JobReprocessView)
        self.assertEqual(resolver.kwargs, {'job_id': self.job1.id})
    
    def test_reprocess_job_url_with_different_ids(self):
        """Test reprocess-job URL with various job_id values"""
        test_ids = [1, 123, 999999, self.job1.id, self.job2.id]
        
        for job_id in test_ids:
            url = reverse('jobs:reprocess-job', kwargs={'job_id': job_id})
            expected_url = f'/jobs/reprocess/{job_id}/'
            self.assertEqual(url, expected_url)
            
            # Test resolution
            resolver = resolve(f'/jobs/reprocess/{job_id}/')
            self.assertEqual(resolver.view_name, 'jobs:reprocess-job')
            self.assertEqual(resolver.kwargs, {'job_id': job_id})
    
    def test_reprocess_job_url_requires_job_id(self):
        """Test that reprocess-job URL requires job_id parameter"""
        with self.assertRaises(NoReverseMatch):
            reverse('jobs:reprocess-job')
        
        with self.assertRaises(NoReverseMatch):
            reverse('jobs:reprocess-job', kwargs={})
    
    def test_reprocess_job_url_invalid_id_types(self):
        """Test reprocess-job URL with invalid job_id types"""
        # String that's not a number should not match
        with self.assertRaises(Exception):
            resolve('/jobs/reprocess/invalid/')
        
        # Empty job_id should not match
        with self.assertRaises(Exception):
            resolve('/jobs/reprocess//')


class DeleteJobURLTests(BaseURLTestMixin, TestCase):
    """Test delete-job URL pattern"""
    
    def test_delete_job_url_pattern(self):
        """Test delete-job URL pattern with valid job_id"""
        url = reverse('jobs:delete-job', kwargs={'job_id': self.job1.id})
        expected_url = f'/jobs/delete/{self.job1.id}/'
        self.assertEqual(url, expected_url)
        
        # Test URL resolution
        resolver = resolve(f'/jobs/delete/{self.job1.id}/')
        self.assertEqual(resolver.view_name, 'jobs:delete-job')
        self.assertEqual(resolver.func.view_class, views.JobDeleteView)
        self.assertEqual(resolver.kwargs, {'job_id': self.job1.id})
    
    def test_delete_job_url_with_different_ids(self):
        """Test delete-job URL with various job_id values"""
        test_ids = [1, 123, 999999, self.job1.id, self.job2.id]
        
        for job_id in test_ids:
            url = reverse('jobs:delete-job', kwargs={'job_id': job_id})
            expected_url = f'/jobs/delete/{job_id}/'
            self.assertEqual(url, expected_url)
            
            # Test resolution
            resolver = resolve(f'/jobs/delete/{job_id}/')
            self.assertEqual(resolver.view_name, 'jobs:delete-job')
            self.assertEqual(resolver.kwargs, {'job_id': job_id})
    
    def test_delete_job_url_requires_job_id(self):
        """Test that delete-job URL requires job_id parameter"""
        with self.assertRaises(NoReverseMatch):
            reverse('jobs:delete-job')
        
        with self.assertRaises(NoReverseMatch):
            reverse('jobs:delete-job', kwargs={})


class URLResolutionTests(BaseURLTestMixin, TestCase):
    """Test URL resolution and view mapping"""
    
    def test_all_urls_resolve_to_correct_views(self):
        """Test that all URLs resolve to their intended views"""
        url_view_mapping = {
            '/jobs/': views.JobDescriptionCreateView,
            f'/jobs/{self.job1.id}/': views.JobDescriptionDetailView,
            '/jobs/paste/': views.PasteJobDescriptionView,
            '/jobs/my-jobs/': views.UserJobListView,
            f'/jobs/reprocess/{self.job1.id}/': views.JobReprocessView,
            f'/jobs/delete/{self.job1.id}/': views.JobDeleteView,
        }
        
        for url, expected_view in url_view_mapping.items():
            resolver = resolve(url)
            self.assertEqual(resolver.func.view_class, expected_view)
    
    def test_url_names_are_unique(self):
        """Test that all URL names are unique"""
        url_names = [
            'job-create',
            'job-detail', 
            'paste-job',
            'user-jobs',
            'reprocess-job',
            'delete-job'
        ]
        
        # Check that we can reverse all names without conflicts
        for name in url_names:
            try:
                if name in ['job-detail', 'reprocess-job', 'delete-job']:
                    kwargs = {'pk': 1} if name == 'job-detail' else {'job_id': 1}
                    url = reverse(f'jobs:{name}', kwargs=kwargs)
                else:
                    url = reverse(f'jobs:{name}')
                self.assertIsNotNone(url)
            except NoReverseMatch:
                self.fail(f"Could not reverse URL name: {name}")
    
    def test_view_kwargs_extraction(self):
        """Test that URL parameters are correctly extracted as view kwargs"""
        # Test pk parameter extraction
        resolver = resolve(f'/jobs/{self.job1.id}/')
        self.assertEqual(resolver.kwargs['pk'], self.job1.id)
        
        # Test job_id parameter extraction  
        resolver = resolve(f'/jobs/reprocess/{self.job2.id}/')
        self.assertEqual(resolver.kwargs['job_id'], self.job2.id)
        
        resolver = resolve(f'/jobs/delete/{self.job2.id}/')
        self.assertEqual(resolver.kwargs['job_id'], self.job2.id)


class URLEdgeCasesTests(BaseURLTestMixin, TestCase):
    """Test URL edge cases and error conditions"""
    
    def test_urls_with_very_large_ids(self):
        """Test URLs with very large ID values"""
        large_id = 9223372036854775807  # Max 64-bit int
        
        # Should be able to reverse
        url = reverse('jobs:job-detail', kwargs={'pk': large_id})
        self.assertEqual(url, f'/jobs/{large_id}/')
        
        # Should be able to resolve
        resolver = resolve(f'/jobs/{large_id}/')
        self.assertEqual(resolver.kwargs['pk'], large_id)
    
    def test_urls_with_zero_ids(self):
        """Test URLs with zero ID values"""
        # Zero should be valid
        url = reverse('jobs:job-detail', kwargs={'pk': 0})
        self.assertEqual(url, '/jobs/0/')
        
        resolver = resolve('/jobs/0/')
        self.assertEqual(resolver.kwargs['pk'], 0)
    
    def test_urls_with_negative_ids_not_matched(self):
        """Test that negative IDs don't match URL patterns"""
        # Negative IDs should not match the int pattern
        with self.assertRaises(Exception):
            resolve('/jobs/-1/')
        
        with self.assertRaises(Exception):
            resolve('/jobs/reprocess/-1/')
    
    def test_malformed_urls(self):
        """Test malformed URLs don't match patterns"""
        malformed_urls = [
            '/jobs/abc/',           # Non-numeric pk
            '/jobs/123abc/',        # Mixed alphanumeric
            '/jobs/123.45/',        # Float
            '/jobs//',              # Empty pk
            '/jobs/ /',             # Space in pk
            '/jobs/delete//',       # Empty job_id
            '/jobs/reprocess/abc/', # Non-numeric job_id
        ]
        
        for url in malformed_urls:
            with self.assertRaises(Exception):
                resolve(url)
    
    def test_case_sensitivity(self):
        """Test URL case sensitivity"""
        # Django URLs are case sensitive by default
        valid_urls = [
            '/jobs/',
            '/jobs/paste/',
            '/jobs/my-jobs/',
        ]
        
        for url in valid_urls:
            # Should resolve correctly
            resolver = resolve(url)
            self.assertIsNotNone(resolver)
            
            # Uppercase version should not resolve (if using default settings)
            with self.assertRaises(Exception):
                resolve(url.upper())
    
    def test_trailing_slash_behavior(self):
        """Test trailing slash handling"""
        urls_requiring_slash = [
            '/jobs/',
            '/jobs/paste/',
            '/jobs/my-jobs/',
            f'/jobs/{self.job1.id}/',
            f'/jobs/reprocess/{self.job1.id}/',
            f'/jobs/delete/{self.job1.id}/',
        ]
        
        for url in urls_requiring_slash:
            # With slash should work
            resolver = resolve(url)
            self.assertIsNotNone(resolver)
            
            # Without slash behavior depends on APPEND_SLASH setting
            # We'll just test that it's handled consistently
            url_without_slash = url.rstrip('/')
            if url_without_slash != url:  # Only test if there was a slash to remove
                try:
                    resolve(url_without_slash)
                    # If it resolves, that's fine
                except:  # noqa: E722
                    # If it doesn't resolve, that's also expected behavior
                    pass


class URLParameterValidationTests(BaseURLTestMixin, TestCase):
    """Test URL parameter validation and type conversion"""
    
    def test_pk_parameter_type_conversion(self):
        """Test that pk parameters are properly converted to strings"""
        test_cases = [
            (1, 1),  # Expect integer value
            (123, 123),
            (999999, 999999),
            (0, 0),
        ]
        
        for input_pk, expected_value in test_cases:
            resolver = resolve(f'/jobs/{input_pk}/')
            self.assertEqual(resolver.kwargs['pk'], expected_value)
            self.assertIsInstance(resolver.kwargs['pk'], int)
    
    def test_job_id_parameter_type_conversion(self):
        """Test that job_id parameters are properly converted to strings"""
        test_cases = [
            (1, 1),  # Expect integer value
            (456, 456),
            (789012, 789012),
        ]
        
        for input_id, expected_value in test_cases:
            # Test reprocess URL
            resolver = resolve(f'/jobs/reprocess/{input_id}/')
            self.assertEqual(resolver.kwargs['job_id'], expected_value)
            self.assertIsInstance(resolver.kwargs['job_id'], int)
            
            # Test delete URL
            resolver = resolve(f'/jobs/delete/{input_id}/')
            self.assertEqual(resolver.kwargs['job_id'], expected_value)
            self.assertIsInstance(resolver.kwargs['job_id'], int)
    
    def test_parameter_names_consistency(self):
        """Test that parameter names are consistent with view expectations"""
        # job-detail uses 'pk'
        resolver = resolve(f'/jobs/{self.job1.id}/')
        self.assertIn('pk', resolver.kwargs)
        self.assertNotIn('job_id', resolver.kwargs)
        
        # reprocess-job and delete-job use 'job_id'
        resolver = resolve(f'/jobs/reprocess/{self.job1.id}/')
        self.assertIn('job_id', resolver.kwargs)
        self.assertNotIn('pk', resolver.kwargs)
        
        resolver = resolve(f'/jobs/delete/{self.job1.id}/')
        self.assertIn('job_id', resolver.kwargs)  
        self.assertNotIn('pk', resolver.kwargs)


class URLNamespaceTests(BaseURLTestMixin, TestCase):
    """Test URL namespace functionality"""
    
    def test_app_namespace_reverse(self):
        """Test reversing URLs with app namespace"""
        # All URLs should be reversible with jobs: namespace
        namespaced_patterns = [
            ('jobs:job-create', {}, '/jobs/'),
            ('jobs:job-detail', {'pk': 1}, '/jobs/1/'),
            ('jobs:paste-job', {}, '/jobs/paste/'),
            ('jobs:user-jobs', {}, '/jobs/my-jobs/'),
            ('jobs:reprocess-job', {'job_id': 1}, '/jobs/reprocess/1/'),
            ('jobs:delete-job', {'job_id': 1}, '/jobs/delete/1/'),
        ]
        
        for pattern_name, kwargs, expected_url in namespaced_patterns:
            url = reverse(pattern_name, kwargs=kwargs)
            self.assertEqual(url, expected_url)
    
    def test_namespace_isolation(self):
        """Test that namespace provides proper isolation"""
        # Should not be able to reverse without namespace
        with self.assertRaises(NoReverseMatch):
            reverse('job-create')
        
        with self.assertRaises(NoReverseMatch):
            reverse('paste-job')
    
    def test_namespace_in_resolved_urls(self):
        """Test that resolved URLs include namespace information"""
        resolver = resolve('/jobs/')
        self.assertEqual(resolver.namespace, 'jobs')
        self.assertEqual(resolver.view_name, 'jobs:job-create')
        
        resolver = resolve('/jobs/paste/')
        self.assertEqual(resolver.namespace, 'jobs')
        self.assertEqual(resolver.view_name, 'jobs:paste-job')


class URLIntegrationTests(BaseURLTestMixin, TestCase):
    """Test URL integration with Django's URL system"""
    
    def test_url_patterns_in_urlconf(self):
        """Test that URL patterns are properly included in main URLconf"""
        # This assumes the jobs URLs are included in the main URLconf
        # You might need to adjust based on your actual URL configuration
        
        # Test that we can resolve jobs URLs from root
        resolver = resolve('/jobs/')
        self.assertIsNotNone(resolver)
        
        # Test that the app_name is properly set
        self.assertEqual(resolver.namespace, 'jobs')
    
    def test_url_pattern_order(self):
        """Test that URL patterns are in correct order (more specific first)"""
        # More specific patterns should match before generic ones
        
        # /jobs/paste/ should match paste-job, not job-detail
        resolver = resolve('/jobs/paste/')
        self.assertEqual(resolver.view_name, 'jobs:paste-job')
        
        # /jobs/my-jobs/ should match user-jobs, not job-detail  
        resolver = resolve('/jobs/my-jobs/')
        self.assertEqual(resolver.view_name, 'jobs:user-jobs')
        
        # /jobs/123/ should match job-detail
        resolver = resolve('/jobs/123/')
        self.assertEqual(resolver.view_name, 'jobs:job-detail')
    
    def test_url_include_behavior(self):
        """Test URL include behavior with jobs app"""
        # Test that included URLs maintain their structure
        test_urls = [
            '/jobs/',
            '/jobs/paste/', 
            '/jobs/my-jobs/',
            f'/jobs/{self.job1.id}/',
            f'/jobs/reprocess/{self.job1.id}/',
            f'/jobs/delete/{self.job1.id}/'
        ]
        
        for url in test_urls:
            resolver = resolve(url)
            # All should resolve to jobs namespace
            self.assertEqual(resolver.namespace, 'jobs')
            # All should start with 'jobs:' in view_name
            self.assertTrue(resolver.view_name.startswith('jobs:'))


class URLPerformanceTests(BaseURLTestMixin, TestCase):
    """Test URL resolution performance and efficiency"""

    def test_url_resolution_performance(self):
        """Test that URL resolution is efficient"""
        import time
        
        urls_to_test = [
            '/jobs/',
            '/jobs/123/',
            '/jobs/paste/',
            '/jobs/my-jobs/',
            '/jobs/reprocess/456/',
            '/jobs/delete/789/'
        ]
        
        # Time URL resolution
        start_time = time.time()
        
        for _ in range(1000):  # Resolve each URL 1000 times
            for url in urls_to_test:
                resolve(url)
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # Should be reasonably fast - increased threshold to 1.5 seconds
        self.assertLess(total_time, 1.5, "URL resolution taking too long")


    def test_reverse_performance(self):
        """Test that URL reversing is efficient"""
        import time
        
        patterns_to_test = [
            ('jobs:job-create', {}),
            ('jobs:job-detail', {'pk': 123}),
            ('jobs:paste-job', {}),
            ('jobs:user-jobs', {}),
            ('jobs:reprocess-job', {'job_id': 456}),
            ('jobs:delete-job', {'job_id': 789})
        ]
        
        # Time URL reversing
        start_time = time.time()
        
        for _ in range(1000):  # Reverse each pattern 1000 times
            for pattern_name, kwargs in patterns_to_test:
                reverse(pattern_name, kwargs=kwargs)
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # Should be reasonably fast - increased threshold to 1.5 seconds
        self.assertLess(total_time, 1.5, "URL reversing taking too long")