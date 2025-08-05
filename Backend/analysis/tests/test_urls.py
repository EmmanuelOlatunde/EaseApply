from django.test import TestCase, SimpleTestCase
from django.urls import reverse, resolve, NoReverseMatch
from django.http import Http404
from analysis.views import GenerateCoverLetterView
from analysis import urls as analysis_urls


class AnalysisURLsTestCase(SimpleTestCase):
    """
    Comprehensive test suite for analysis URLs configuration.
    Tests URL patterns, namespacing, resolution, and routing behavior.
    """
    
    def test_app_name_is_set(self):
        """Test that the app_name is correctly set to 'analysis'"""
        self.assertEqual(analysis_urls.app_name, 'analysis')
    
    def test_urlpatterns_exist(self):
        """Test that urlpatterns is defined and not empty"""
        self.assertTrue(hasattr(analysis_urls, 'urlpatterns'))
        self.assertIsInstance(analysis_urls.urlpatterns, list)
        self.assertGreater(len(analysis_urls.urlpatterns), 0)
    
    def test_generate_cover_letter_url_pattern_exists(self):
        """Test that generate-cover-letter URL pattern exists"""
        url_names = [pattern.name for pattern in analysis_urls.urlpatterns if hasattr(pattern, 'name')]
        self.assertIn('generate-cover-letter', url_names)
    
    def test_generate_cover_letter_url_resolves_correctly(self):
        """Test that the generate-cover-letter URL resolves to correct path"""
        url = reverse('analysis:generate-cover-letter')
        self.assertEqual(url, '/api/analysis/generate-cover-letter/')
    
    def test_generate_cover_letter_url_resolves_to_correct_view(self):
        """Test that URL resolves to the correct view class"""
        resolved = resolve('/api/analysis/generate-cover-letter/')
        self.assertEqual(resolved.func.view_class, GenerateCoverLetterView)
    
    def test_generate_cover_letter_view_name_resolution(self):
        """Test that the view name resolves correctly"""
        resolved = resolve('/api/analysis/generate-cover-letter/')
        self.assertEqual(resolved.view_name, 'analysis:generate-cover-letter')
    
    def test_generate_cover_letter_url_namespace(self):
        """Test that the URL uses the correct namespace"""
        resolved = resolve('/api/analysis/generate-cover-letter/')
        self.assertEqual(resolved.namespace, 'analysis')
    
    def test_generate_cover_letter_url_pattern_name(self):
        """Test that the URL pattern has the correct name"""
        resolved = resolve('/api/analysis/generate-cover-letter/')
        self.assertEqual(resolved.url_name, 'generate-cover-letter')
    
    def test_reverse_url_generation(self):
        """Test reverse URL generation works correctly"""
        # Test with namespace
        url_with_namespace = reverse('analysis:generate-cover-letter')
        self.assertEqual(url_with_namespace, '/api/analysis/generate-cover-letter/')
        
        # Verify the reversed URL actually resolves back
        resolved = resolve(url_with_namespace)
        self.assertEqual(resolved.view_name, 'analysis:generate-cover-letter')
    
    def test_url_path_format(self):
        """Test that URL path follows expected format"""
        resolved = resolve('/api/analysis/generate-cover-letter/')
        # Verify no arguments or keyword arguments are expected
        self.assertEqual(resolved.args, ())
        self.assertEqual(resolved.kwargs, {})
    
    def test_url_pattern_specificity(self):
        """Test that the URL pattern is specific and doesn't match unintended paths"""
        # These should NOT resolve to our view
        invalid_paths = [
            '/api/analysis/generate-cover-letter',  # Missing trailing slash
            '/api/analysis/generate-cover-letter/extra/',  # Extra path
            '/api/analysis/generate-cover-letters/',  # Plural
            '/api/analysis/generate_cover_letter/',  # Underscore instead of hyphen
            '/api/analysis/cover-letter/',  # Missing generate
            '/generate-cover-letter/',  # Missing analysis prefix
        ]
        
        for invalid_path in invalid_paths:
            with self.assertRaises(Http404):
                resolve(invalid_path)
    
    def test_url_case_sensitivity(self):
        """Test URL case sensitivity"""
        # Django URLs are case-sensitive, these should not match
        case_variants = [
            '/api/analysis/Generate-Cover-Letter/',
            '/api/analysis/GENERATE-COVER-LETTER/',
            '/Analysis/generate-cover-letter/',
            '/ANALYSIS/generate-cover-letter/',
        ]
        
        for variant in case_variants:
            with self.assertRaises(Http404):
                resolve(variant)
    
    def test_trailing_slash_behavior(self):
        """Test trailing slash behavior"""
        # With trailing slash should work
        resolved_with_slash = resolve('/api/analysis/generate-cover-letter/')
        self.assertEqual(resolved_with_slash.view_name, 'analysis:generate-cover-letter')
        
        # Without trailing slash should raise Http404 (since pattern has trailing slash)
        with self.assertRaises(Http404):
            resolve('/api/analysis/generate-cover-letter')
    
    def test_url_pattern_type(self):
        """Test that URL pattern is properly configured"""
        pattern = analysis_urls.urlpatterns[0]  # Assuming it's the first pattern
        
        # Check it's a URLPattern (not URLResolver)
        from django.urls.resolvers import URLPattern
        self.assertIsInstance(pattern, URLPattern)
        
        # Check pattern attributes
        self.assertEqual(pattern.name, 'generate-cover-letter')
        self.assertEqual(pattern.callback.view_class, GenerateCoverLetterView)
    
    def test_import_structure(self):
        """Test that the URLs module imports are correct"""
        # Test that required imports exist
        self.assertTrue(hasattr(analysis_urls, 'path'))
        self.assertTrue(hasattr(analysis_urls, 'GenerateCoverLetterView'))
        
        # Test that the view is imported from the correct module
        from analysis.views import GenerateCoverLetterView as DirectImport
        self.assertEqual(analysis_urls.GenerateCoverLetterView, DirectImport)
    
    def test_url_configuration_completeness(self):
        """Test that all required URL configurations are present"""
        # Verify we have exactly one URL pattern (based on your current urls.py)
        self.assertEqual(len(analysis_urls.urlpatterns), 1)
        
        # Verify the pattern configuration
        pattern = analysis_urls.urlpatterns[0]
        self.assertEqual(str(pattern.pattern), 'generate-cover-letter/')
        self.assertEqual(pattern.name, 'generate-cover-letter')
    
    def test_reverse_lazy_compatibility(self):
        """Test that URLs work with reverse_lazy for class-based views"""
        from django.urls import reverse_lazy
        
        lazy_url = reverse_lazy('analysis:generate-cover-letter')
        # reverse_lazy returns a lazy object, but should resolve to the same URL
        self.assertEqual(str(lazy_url), '/api/analysis/generate-cover-letter/')
    
    def test_url_regex_patterns(self):
        """Test URL pattern matching behavior"""
        # Test that only exact matches work
        valid_url = '/api/analysis/generate-cover-letter/'
        resolved = resolve(valid_url)
        self.assertEqual(resolved.view_name, 'analysis:generate-cover-letter')
        
        # Test that partial matches don't work
        [
            '/api/analysis/generate-cover-letter/anything',
            '/api/analysis/generate-cover-letter/?param=value',  # Query params are OK though
        ]
        
        # Only the first should fail, query params are handled by Django separately
        with self.assertRaises(Http404):
            resolve('/api/analysis/generate-cover-letter/anything')
        
        # Query params should still resolve correctly
        resolved_with_params = resolve('/api/analysis/generate-cover-letter/')
        self.assertEqual(resolved_with_params.view_name, 'analysis:generate-cover-letter')
    
    def test_nonexistent_url_reverse(self):
        """Test that trying to reverse non-existent URLs raises appropriate errors"""
        with self.assertRaises(NoReverseMatch):
            reverse('analysis:nonexistent-url')
        
        with self.assertRaises(NoReverseMatch):
            reverse('wrong-namespace:generate-cover-letter')
    
    def test_url_view_class_integration(self):
        """Test that the URL properly integrates with the view class"""
        resolved = resolve('/api/analysis/generate-cover-letter/')
        
        # Verify the view class is properly set
        self.assertTrue(hasattr(resolved.func, 'view_class'))
        self.assertEqual(resolved.func.view_class, GenerateCoverLetterView)
        
        # Verify it's using as_view() method
        self.assertTrue(callable(resolved.func))
    
    def test_url_pattern_kwargs_and_args(self):
        """Test that URL pattern doesn't expect any arguments"""
        resolved = resolve('/api/analysis/generate-cover-letter/')
        
        # Should have no positional or keyword arguments
        self.assertEqual(len(resolved.args), 0)
        self.assertEqual(len(resolved.kwargs), 0)
    
    def test_module_level_attributes(self):
        """Test module-level attributes are correctly set"""
        # Test app_name
        self.assertTrue(hasattr(analysis_urls, 'app_name'))
        self.assertIsInstance(analysis_urls.app_name, str)
        self.assertEqual(analysis_urls.app_name, 'analysis')
        
        # Test urlpatterns
        self.assertTrue(hasattr(analysis_urls, 'urlpatterns'))
        self.assertIsInstance(analysis_urls.urlpatterns, list)
    
    def test_url_string_representation(self):
        """Test string representation of URL patterns"""
        pattern = analysis_urls.urlpatterns[0]
        
        # Test that pattern has proper string representation
        pattern_str = str(pattern.pattern)
        self.assertEqual(pattern_str, 'generate-cover-letter/')
        
        # Test pattern name
        self.assertEqual(pattern.name, 'generate-cover-letter')


class URLsIntegrationTestCase(TestCase):
    """
    Integration tests for URLs that may require database access.
    These tests ensure URLs work correctly in a full Django environment.
    """
    
    def test_url_accessible_through_client(self):
        """Test that URL is accessible through Django test client"""
        from django.test import Client
        
        client = Client()
        # We expect this to fail with 401 (unauthorized) or 405 (method not allowed for GET)
        # but NOT with 404 (URL not found)
        response = client.get('/api/analysis/generate-cover-letter/')
        
        # Should not be 404 - URL should be found
        self.assertNotEqual(response.status_code, 404)
        # Will likely be 401 (unauthorized) or 405 (method not allowed)
        self.assertIn(response.status_code, [401, 405])
    
    def test_url_in_django_admin_context(self):
        """Test URL resolution in Django admin context (if applicable)"""
        # This tests that URLs work in various Django contexts
        url = reverse('analysis:generate-cover-letter')
        self.assertIsInstance(url, str)
        self.assertTrue(url.startswith('/'))
    
    def test_url_middleware_compatibility(self):
        """Test that URLs work with Django middleware"""
        from django.test import Client
        
        client = Client()
        # Test that middleware processes the URL correctly
        response = client.get('/api/analysis/generate-cover-letter/')
        
        # Should have standard middleware headers (even if request fails)
        # This tests middleware compatibility
        self.assertNotEqual(response.status_code, 404)


class URLsEdgeCaseTestCase(SimpleTestCase):
    """Test edge cases and potential gotchas in URL configuration"""
    
    def test_unicode_url_handling(self):
        """Test that URLs handle unicode correctly (though our URLs are ASCII)"""
        # Our URLs are ASCII, but test the resolution mechanism
        url = reverse('analysis:generate-cover-letter')
        self.assertIsInstance(url, str)
        
        # Ensure URL is ASCII-only as expected
        url.encode('ascii')  # Should not raise UnicodeEncodeError
    
    def test_url_pattern_ordering(self):
        """Test that URL patterns are in correct order (more specific first)"""
        # Since we only have one pattern, this tests the general principle
        patterns = analysis_urls.urlpatterns
        
        # Verify we have the expected number of patterns
        self.assertEqual(len(patterns), 1)
        
        # Verify the pattern is specific enough
        pattern = patterns[0]
        pattern_str = str(pattern.pattern)
        self.assertNotEqual(pattern_str, '')  # Should not be catch-all
        self.assertNotIn('.*', pattern_str)   # Should not be overly broad regex
    
    def test_url_security_implications(self):
        """Test URL patterns don't introduce security issues"""
        pattern = analysis_urls.urlpatterns[0]
        pattern_str = str(pattern.pattern)
        
        # Should not allow directory traversal
        self.assertNotIn('..', pattern_str)
        
        # Should not have overly permissive regex
        self.assertNotIn('.*', pattern_str)
        self.assertNotIn('.+', pattern_str)
        
        # Should be specific
        self.assertTrue(len(pattern_str) > 5)  # Reasonable specificity
    
    def test_url_performance_considerations(self):
        """Test URL patterns are optimized for performance"""
        # Test that URL resolution is fast (no complex regex)
        import time
        
        start_time = time.time()
        for _ in range(100):
            resolve('/api/analysis/generate-cover-letter/')
        end_time = time.time()
        
        # Should resolve quickly (less than 0.1 seconds for 100 resolutions)
        self.assertLess(end_time - start_time, 0.1)
    
    def test_url_pattern_immutability(self):
        """Test that URL patterns don't change unexpectedly"""
        # Capture current state
        original_patterns = list(analysis_urls.urlpatterns)
        original_app_name = analysis_urls.app_name
        
        # Verify they haven't changed
        self.assertEqual(analysis_urls.urlpatterns, original_patterns)
        self.assertEqual(analysis_urls.app_name, original_app_name)
        
        # Test pattern details haven't changed
        pattern = analysis_urls.urlpatterns[0]
        self.assertEqual(str(pattern.pattern), 'generate-cover-letter/')
        self.assertEqual(pattern.name, 'generate-cover-letter')
        self.assertEqual(pattern.callback.view_class, GenerateCoverLetterView)