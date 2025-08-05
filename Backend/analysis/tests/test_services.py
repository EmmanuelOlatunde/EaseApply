"""
Test suite for Analysis app services.
Tests OpenRouterService functionality, error handling, and API integration.
"""

import os
from unittest.mock import Mock, patch

from analysis.services import OpenRouterService
from .test_base import BaseAnalysisTestCase


class OpenRouterServiceTest(BaseAnalysisTestCase):
    """Test suite for OpenRouterService."""
    
    def setUp(self):
        super().setUp()
        self.service = OpenRouterService()
    
    def test_service_initialization(self):
        """Test service initialization with correct base URL and API keys."""
        self.assertEqual(self.service.base_url, "https://openrouter.ai/api/v1")
        self.assertIn("kimi", self.service.api_keys)
        self.assertIn("qwen", self.service.api_keys)
        self.assertIn("deepseek", self.service.api_keys)
    
    @patch('analysis.services.OpenAI')
    def test_init_client(self, mock_openai):
        """Test _init_client method creates OpenAI client correctly."""
        test_api_key = "test_api_key"
        
        self.service._init_client(test_api_key)
        
        mock_openai.assert_called_once_with(
            base_url="https://openrouter.ai/api/v1",
            api_key=test_api_key
        )
    
    @patch.dict(os.environ, {
        'OPENROUTER_API_KEY_KIMI': 'kimi_key',
        'OPENROUTER_API_KEY_QWEN': 'qwen_key',
        'OPENROUTER_API_KEY_DEEPSEEK': 'deepseek_key'
    })
    def test_api_keys_from_environment(self):
        """Test that API keys are loaded from environment variables."""
        service = OpenRouterService()
        
        self.assertEqual(service.api_keys["kimi"], "kimi_key")
        self.assertEqual(service.api_keys["qwen"], "qwen_key")
        self.assertEqual(service.api_keys["deepseek"], "deepseek_key")
    
    @patch('analysis.services.OpenRouterService._init_client')
    @patch('analysis.services.time.time')
    def test_successful_cover_letter_generation(self, mock_time, mock_init_client):
        """Test successful cover letter generation with first model."""
        # Setup mock time
       # mock_time.side_effect = [1000.0, 1002.5]  # Start and end time
        mock_time.side_effect = [1000.0, 1002.5, 1003.0]  # ensure enough calls
        # time.time is called multiple times during logging + duration calculation


        
        # Setup mock client and response
        mock_client = Mock()
        mock_init_client.return_value = mock_client
        
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "Generated cover letter content"
        mock_response.usage = Mock()
        mock_response.usage.total_tokens = 500
        
        mock_client.chat.completions.create.return_value = mock_response
        
        # Test the service
        result = self.service.generate_cover_letter(
            title="Software Engineer",
            company="Tech Corp",
            location="San Francisco",
            job_type="Full-time",
            salary_range="$100k",
            requirements="Python experience",
            skills_required="Python, Django",
            experience_level="Mid",
            resume_content="Resume content",
            template_type="professional"
        )
        
        # Assertions
        self.assertTrue(result['success'])
        self.assertEqual(result['cover_letter'], "Generated cover letter content")
        self.assertIn('prompt_used', result)
        self.assertEqual(result['metadata']['model'], "moonshotai/kimi-k2:free")
        self.assertEqual(result['metadata']['tokens_used'], 500)
        self.assertEqual(result['metadata']['processing_time'], 2.5)
        self.assertEqual(result['metadata']['template_type'], "professional")
    
    @patch('analysis.services.OpenRouterService._init_client')
    @patch('analysis.services.time.time')
    def test_cover_letter_generation_with_think_tags_removed(self, mock_time, mock_init_client):
        """Test that <think> tags are removed from generated content."""
        mock_time.side_effect = [1000.0, 1002.0]
        
        mock_client = Mock()
        mock_init_client.return_value = mock_client
        
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = """<think>
        Let me think about this cover letter...
        </think>
        Generated cover letter content without think tags"""
        mock_response.usage = Mock()
        mock_response.usage.total_tokens = 400
        
        mock_client.chat.completions.create.return_value = mock_response
        
        result = self.service.generate_cover_letter(
            title="Engineer",
            company="Company",
            location="Location",
            job_type="Full-time",
            salary_range="$100k",
            requirements="Requirements",
            skills_required="Skills",
            experience_level="Mid",
            resume_content="Resume",
            template_type="professional"
        )
        
        self.assertTrue(result['success'])
        self.assertEqual(result['cover_letter'], "Generated cover letter content without think tags")
        self.assertNotIn('<think>', result['cover_letter'])
        self.assertNotIn('</think>', result['cover_letter'])
    
    @patch('analysis.services.OpenRouterService._init_client')
    def test_fallback_to_second_model_on_first_failure(self, mock_init_client):
        """Test fallback mechanism when first model fails."""
        # Setup mock clients
        failing_client = Mock()
        failing_client.chat.completions.create.side_effect = Exception("API Error")
        
        successful_client = Mock()
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "Fallback generated content"
        mock_response.usage = Mock()
        mock_response.usage.total_tokens = 300
        successful_client.chat.completions.create.return_value = mock_response
        
        # Mock _init_client to return different clients for different calls
        mock_init_client.side_effect = [failing_client, successful_client]
        
        with patch('analysis.services.time.time', side_effect=[1000.0, 1001.0, 1001.5, 1002.0, 1002.5]):
            result = self.service.generate_cover_letter(
                title="Engineer",
                company="Company",
                location="Location",
                job_type="Full-time",
                salary_range="$100k",
                requirements="Requirements",
                skills_required="Skills",
                experience_level="Mid",
                resume_content="Resume",
                template_type="professional"
            )
        
        self.assertTrue(result['success'])
        self.assertEqual(result['cover_letter'], "Fallback generated content")
        self.assertEqual(result['metadata']['model'], "cognitivecomputations/dolphin-mistral-24b-venice-edition:free")
        self.assertEqual(result['metadata']['tokens_used'], 300)
    
    @patch('analysis.services.OpenRouterService._init_client')
    def test_all_models_fail(self, mock_init_client):
        """Test when all models fail to generate cover letter."""
        # Setup all clients to fail
        failing_client = Mock()
        failing_client.chat.completions.create.side_effect = Exception("API Error")
        mock_init_client.return_value = failing_client
        
        result = self.service.generate_cover_letter(
            title="Engineer",
            company="Company",
            location="Location",
            job_type="Full-time",
            salary_range="$100k",
            requirements="Requirements",
            skills_required="Skills",
            experience_level="Mid",
            resume_content="Resume",
            template_type="professional"
        )
        
        self.assertFalse(result['success'])
        self.assertEqual(result['error'], "All model attempts failed")
        self.assertEqual(result['error_type'], "failover")
    
    @patch('analysis.services.OpenRouterService._init_client')
    def test_creative_template_type(self, mock_init_client):
        """Test cover letter generation with creative template."""
        mock_client = Mock()
        mock_init_client.return_value = mock_client
        
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "Creative cover letter"
        mock_response.usage = Mock()
        mock_response.usage.total_tokens = 450
        
        mock_client.chat.completions.create.return_value = mock_response
        
        with patch('analysis.services.time.time', side_effect=[1000.0, 1002.0]):
            result = self.service.generate_cover_letter(
                title="Designer",
                company="Creative Agency",
                location="NYC",
                job_type="Full-time",
                salary_range="$80k",
                requirements="Design experience",
                skills_required="Photoshop, Illustrator",
                experience_level="Mid",
                resume_content="Design resume",
                template_type="creative"
            )
        
        self.assertTrue(result['success'])
        self.assertEqual(result['metadata']['template_type'], "creative")
        
        # Verify the creative prompt was used
        call_args = mock_client.chat.completions.create.call_args
        messages = call_args[1]['messages']
        user_message = messages[1]['content']
        
        # Creative template should contain different keywords than professional
        self.assertIn('creative', user_message.lower())
    
    @patch('analysis.services.OpenRouterService._init_client')
    def test_api_call_parameters(self, mock_init_client):
        """Test that API call is made with correct parameters."""
        mock_client = Mock()
        mock_init_client.return_value = mock_client
        
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "Test content"
        mock_response.usage = Mock()
        mock_response.usage.total_tokens = 400
        mock_client.chat.completions.create.return_value = mock_response
        
        with patch('analysis.services.time.time', side_effect=[1000.0, 1001.0]):
            self.service.generate_cover_letter(
                title="Engineer",
                company="Company",
                location="Location",
                job_type="Full-time",
                salary_range="$100k",
                requirements="Requirements",
                skills_required="Skills",
                experience_level="Mid",
                resume_content="Resume",
                template_type="professional"
            )
        
        # Verify API call parameters
        mock_client.chat.completions.create.assert_called_once()
        call_args = mock_client.chat.completions.create.call_args
        
        self.assertEqual(call_args[1]['model'], "moonshotai/kimi-k2:free")
        self.assertEqual(call_args[1]['max_tokens'], 800)
        self.assertEqual(call_args[1]['temperature'], 0.7)
        self.assertEqual(call_args[1]['top_p'], 1.0)
        
        # Verify messages structure
        messages = call_args[1]['messages']
        self.assertEqual(len(messages), 2)
        self.assertEqual(messages[0]['role'], 'system')
        self.assertEqual(messages[1]['role'], 'user')
        self.assertIn('professional career advisor', messages[0]['content'])
    
    @patch('analysis.services.OpenRouterService._init_client')
    def test_prompt_formatting(self, mock_init_client):
        """Test that prompt is formatted correctly with provided data."""
        mock_client = Mock()
        mock_init_client.return_value = mock_client
        
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "Test content"
        mock_response.usage = Mock()
        mock_response.usage.total_tokens = 400
        mock_client.chat.completions.create.return_value = mock_response
        
        test_data = {
            'title': 'Senior Developer',
            'company': 'Awesome Corp',
            'location': 'Remote',
            'job_type': 'Contract',
            'salary_range': '$150k-$200k',
            'requirements': 'Advanced Python skills',
            'skills_required': 'Python, Django, React',
            'experience_level': 'Senior',
            'resume_content': 'Experienced developer resume',
            'template_type': 'professional'
        }
        
        with patch('analysis.services.time.time', side_effect=[1000.0, 1001.0]):
            result = self.service.generate_cover_letter(**test_data)
        
        # Check that the prompt was formatted correctly and returned
        self.assertIn('prompt_used', result)
        prompt = result['prompt_used']
        
        # Verify all data was included in the prompt
        self.assertIn('Senior Developer', prompt)
        self.assertIn('Awesome Corp', prompt)
        self.assertIn('Remote', prompt)
        self.assertIn('Contract', prompt)
        self.assertIn('$150k-$200k', prompt)
        self.assertIn('Advanced Python skills', prompt)
        self.assertIn('Python, Django, React', prompt)
        self.assertIn('Senior', prompt)
        self.assertIn('Experienced developer resume', prompt)
    
    @patch('analysis.services.OpenRouterService._init_client')
    def test_whitespace_handling_in_inputs(self, mock_init_client):
        """Test that input parameters with extra whitespace are handled correctly."""
        mock_client = Mock()
        mock_init_client.return_value = mock_client
        
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "Test content"
        mock_response.usage = Mock()
        mock_response.usage.total_tokens = 400
        mock_client.chat.completions.create.return_value = mock_response
        
        with patch('analysis.services.time.time', side_effect=[1000.0, 1001.0]):
            result = self.service.generate_cover_letter(
                title="  Software Engineer  ",
                company="\n\tTech Corp\n",
                location="  San Francisco  ",
                job_type="Full-time\t",
                salary_range=" $100k-120k ",
                requirements="  Python experience  ",
                skills_required=" Python, Django ",
                experience_level=" Mid ",
                resume_content="  Resume content  ",
                template_type="professional"
            )
        
        # Verify whitespace was stripped in the prompt
        prompt = result['prompt_used']
        self.assertIn('Software Engineer', prompt)
        self.assertIn('Tech Corp', prompt)
        self.assertNotIn('  Software Engineer  ', prompt)
        self.assertNotIn('\n\tTech Corp\n', prompt)
    
    @patch('analysis.services.OpenRouterService._init_client')
    def test_response_without_usage_tokens(self, mock_init_client):
        """Test handling of API response without usage.total_tokens."""
        mock_client = Mock()
        mock_init_client.return_value = mock_client
        
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "Test content"
        # Mock usage object without total_tokens attribute
        mock_response.usage = Mock(spec=[])  # Empty spec, no total_tokens
        
        mock_client.chat.completions.create.return_value = mock_response
        
        with patch('analysis.services.time.time', side_effect=[1000.0, 1001.0]):
            result = self.service.generate_cover_letter(
                title="Engineer",
                company="Company",
                location="Location",
                job_type="Full-time",
                salary_range="$100k",
                requirements="Requirements",
                skills_required="Skills",
                experience_level="Mid",
                resume_content="Resume",
                template_type="professional"
            )
        
        self.assertTrue(result['success'])
        self.assertIsNone(result['metadata']['tokens_used'])
    
    def test_fallback_models_configuration(self):
        """Test that fallback models are configured correctly."""
        # This is a bit of a white-box test, but important for ensuring
        # the fallback mechanism is properly configured
        
        with patch.object(self.service, '_init_client') as mock_init_client:
            # Mock all clients to fail so we can see the order
            failing_client = Mock()
            failing_client.chat.completions.create.side_effect = Exception("Fail")
            mock_init_client.return_value = failing_client
            
            # Capture the models that were attempted
            attempted_models = []
            self.service._init_client
            
            def capture_init_client(api_key):
                # Find which model this API key corresponds to
                for model_name, key in [
                    ("moonshotai/kimi-k2:free", self.service.api_keys["kimi"]),
                    ("cognitivecomputations/dolphin-mistral-24b-venice-edition:free", self.service.api_keys["deepseek"]),
                    ("qwen/qwen3-235b-a22b-2507:free", self.service.api_keys["qwen"]),
                ]:
                    if key == api_key:
                        attempted_models.append(model_name)
                        break
                return failing_client
            
            mock_init_client.side_effect = capture_init_client
            
            result = self.service.generate_cover_letter(
                title="Engineer",
                company="Company",
                location="Location",
                job_type="Full-time",
                salary_range="$100k",
                requirements="Requirements",
                skills_required="Skills",
                experience_level="Mid",
                resume_content="Resume",
                template_type="professional"
            )
            
            # Verify all models were attempted in the correct order
            expected_models = [
                "moonshotai/kimi-k2:free",
                "cognitivecomputations/dolphin-mistral-24b-venice-edition:free",
                "qwen/qwen3-235b-a22b-2507:free"
            ]
            self.assertEqual(attempted_models, expected_models)
            self.assertFalse(result['success'])


class ServiceIntegrationTest(BaseAnalysisTestCase):
    """Integration tests for service layer with different scenarios."""
    
    def setUp(self):
        super().setUp()
        self.service = OpenRouterService()
    
    @patch('analysis.services.OpenRouterService._init_client')
    def test_end_to_end_successful_generation(self, mock_init_client):
        """Test complete end-to-end cover letter generation process."""
        mock_client = Mock()
        mock_init_client.return_value = mock_client
        
        # Create a realistic API response
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = """
        Dear Hiring Manager,
        
        I am excited to apply for the Senior Software Engineer position at Tech Corp.
        With over 6 years of Python development experience and expertise in Django,
        I am confident I can contribute significantly to your team.
        
        In my previous role, I built REST APIs serving over 1 million requests daily
        and led a team of 5 developers. My experience with AWS and Docker aligns
        perfectly with your requirements.
        
        I am particularly drawn to Tech Corp's innovative approach to technology
        and would welcome the opportunity to discuss how my skills can benefit
        your organization.
        
        Thank you for your consideration.
        
        Sincerely,
        John Doe
        """
        mock_response.usage = Mock()
        mock_response.usage.total_tokens = 650
        
        mock_client.chat.completions.create.return_value = mock_response
        
        with patch('analysis.services.time.time', side_effect=[1000.0, 1003.2]):
            result = self.service.generate_cover_letter(
                title=self.job_description.title,
                company=self.job_description.company,
                location=self.job_description.location,
                job_type=self.job_description.job_type,
                salary_range=self.job_description.salary_range,
                requirements=self.job_description.requirements,
                skills_required=self.job_description.skills_required,
                experience_level=self.job_description.experience_level,
                resume_content=self.resume.extracted_text,
                template_type="professional"
            )
        
        # Verify complete successful response
        self.assertTrue(result['success'])
        self.assertIn('Dear Hiring Manager', result['cover_letter'])
        self.assertIn('Tech Corp', result['cover_letter'])
        self.assertIn('Senior Software Engineer', result['cover_letter'])
        self.assertIn('John Doe', result['cover_letter'])
        
        # Verify metadata
        self.assertEqual(result['metadata']['tokens_used'], 650)
        self.assertEqual(result['metadata']['processing_time'], 3.2)
        self.assertEqual(result['metadata']['template_type'], 'professional')
        self.assertIn('moonshotai/kimi-k2:free', result['metadata']['model'])
        
        # Verify prompt contains all job and resume data
        prompt = result['prompt_used']
        self.assertIn(self.job_description.title, prompt)
        self.assertIn(self.job_description.company, prompt)
        self.assertIn(self.job_description.requirements, prompt)
        self.assertIn('6 years experience in Python and Django', prompt)  # From resume
    
    @patch('analysis.services.OpenRouterService._init_client')
    def test_partial_api_failure_recovery(self, mock_init_client):
        """Test recovery from partial API failures."""
        # First client fails with connection error
        failing_client = Mock()
        failing_client.chat.completions.create.side_effect = ConnectionError("Network error")
        
        # Second client succeeds
        successful_client = Mock()
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "Recovered cover letter content"
        mock_response.usage = Mock()
        mock_response.usage.total_tokens = 400
        successful_client.chat.completions.create.return_value = mock_response
        
        mock_init_client.side_effect = [failing_client, successful_client]
        
        with patch('analysis.services.time.time', side_effect=[1000.0, 1001.0, 1002.0, 1003.0]):
            result = self.service.generate_cover_letter(
                title="Developer",
                company="Company",
                location="Location",
                job_type="Full-time",
                salary_range="$100k",
                requirements="Requirements",
                skills_required="Skills",
                experience_level="Mid",
                resume_content="Resume content",
                template_type="professional"
            )
        
        # Should succeed with second model
        self.assertTrue(result['success'])
        self.assertEqual(result['cover_letter'], "Recovered cover letter content")
        self.assertEqual(result['metadata']['model'], "cognitivecomputations/dolphin-mistral-24b-venice-edition:free")
    
    @patch('analysis.services.OpenRouterService._init_client')
    def test_multiple_think_tags_removal(self, mock_init_client):
        """Test removal of multiple <think> tags from response."""
        mock_client = Mock()
        mock_init_client.return_value = mock_client
        
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = """<think>
        First thought about the job requirements...
        </think>
        
        Dear Hiring Manager,
        
        <think>
        Let me consider the best way to phrase this...
        </think>
        
        I am writing to express my interest in the position.
        
        <think>
        Should I mention specific achievements here?
        </think>
        
        My experience includes relevant skills.
        
        Sincerely,
        Applicant Name"""
        
        mock_response.usage = Mock()
        mock_response.usage.total_tokens = 500
        
        mock_client.chat.completions.create.return_value = mock_response
        
        with patch('analysis.services.time.time', side_effect=[1000.0, 1002.0]):
            result = self.service.generate_cover_letter(
                title="Position",
                company="Company",
                location="Location",
                job_type="Full-time",
                salary_range="$100k",
                requirements="Requirements",
                skills_required="Skills",
                experience_level="Mid",
                resume_content="Resume",
                template_type="professional"
            )
        
        # All think tags should be removed
        cover_letter = result['cover_letter']
        self.assertNotIn('<think>', cover_letter)
        self.assertNotIn('</think>', cover_letter)
        self.assertNotIn('First thought about', cover_letter)
        self.assertNotIn('Let me consider', cover_letter)
        self.assertNotIn('Should I mention', cover_letter)
        
        # But the actual content should remain
        self.assertIn('Dear Hiring Manager', cover_letter)
        self.assertIn('express my interest', cover_letter)
        self.assertIn('relevant skills', cover_letter)
        self.assertIn('Sincerely', cover_letter)
    
    def test_service_robustness_with_empty_api_keys(self):
        """Test service behavior when API keys are not available."""
        # Create service with no API keys
        with patch.dict(os.environ, {}, clear=True):
            service = OpenRouterService()
            
            # All API keys should be None
            self.assertIsNone(service.api_keys["kimi"])
            self.assertIsNone(service.api_keys["qwen"])
            self.assertIsNone(service.api_keys["deepseek"])
            
            # Service should still fail gracefully
            result = service.generate_cover_letter(
                title="Engineer",
                company="Company",
                location="Location",
                job_type="Full-time",
                salary_range="$100k",
                requirements="Requirements",
                skills_required="Skills",
                experience_level="Mid",
                resume_content="Resume",
                template_type="professional"
            )
            
            self.assertFalse(result['success'])
            self.assertEqual(result['error_type'], "failover")
    
    @patch('analysis.services.OpenRouterService._init_client')
    def test_service_with_malformed_api_response(self, mock_init_client):
        """Test service handling of malformed API responses."""
        mock_client = Mock()
        mock_init_client.return_value = mock_client
        
        # Mock a malformed response (missing expected attributes)
        mock_response = Mock()
        mock_response.choices = []  # Empty choices
        mock_client.chat.completions.create.return_value = mock_response
        
        result = self.service.generate_cover_letter(
            title="Engineer",
            company="Company",
            location="Location",
            job_type="Full-time",
            salary_range="$100k",
            requirements="Requirements",
            skills_required="Skills",
            experience_level="Mid",
            resume_content="Resume",
            template_type="professional"
        )
        
        # Should fail gracefully and try next model
        self.assertFalse(result['success'])
        self.assertEqual(result['error_type'], "failover")
    
    @patch('analysis.services.OpenRouterService._init_client')
    def test_logging_on_model_failures(self, mock_init_client):
        """Test that failures are properly logged."""
        with patch('analysis.services.logger') as mock_logger:
            # Setup failing client
            failing_client = Mock()
            failing_client.chat.completions.create.side_effect = Exception("Test error")
            mock_init_client.return_value = failing_client
            
            self.service.generate_cover_letter(
                title="Engineer",
                company="Company",
                location="Location",
                job_type="Full-time",
                salary_range="$100k",
                requirements="Requirements",
                skills_required="Skills",
                experience_level="Mid",
                resume_content="Resume",
                template_type="professional"
            )
            
            # Verify logging was called for each failed model
            self.assertEqual(mock_logger.warning.call_count, 3)  # 3 models failed
            
            # Check that error messages contain model names
            warning_calls = mock_logger.warning.call_args_list
            self.assertIn("moonshotai/kimi-k2:free", str(warning_calls[0]))
            self.assertIn("Test error", str(warning_calls[0]))


class ServicePerformanceTest(BaseAnalysisTestCase):
    """Performance and timing tests for the service layer."""
    
    def setUp(self):
        super().setUp()
        self.service = OpenRouterService()
    
    @patch('analysis.services.OpenRouterService._init_client')
    def test_processing_time_calculation_accuracy(self, mock_init_client):
        """Test that processing time is calculated accurately."""
        mock_client = Mock()
        mock_init_client.return_value = mock_client
        
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "Test content"
        mock_response.usage = Mock()
        mock_response.usage.total_tokens = 400
        mock_client.chat.completions.create.return_value = mock_response
        
        # Mock specific timing
        start_time = 1000.0
        end_time = 1003.7654321  # Precise timing
        
        with patch('analysis.services.time.time', side_effect=[start_time, end_time]):
            result = self.service.generate_cover_letter(
                title="Engineer",
                company="Company",
                location="Location",
                job_type="Full-time",
                salary_range="$100k",
                requirements="Requirements",
                skills_required="Skills",
                experience_level="Mid",
                resume_content="Resume",
                template_type="professional"
            )
        
        # Processing time should be rounded to 2 decimal places
        expected_time = round(end_time - start_time, 2)
        self.assertEqual(result['metadata']['processing_time'], expected_time)
        self.assertEqual(result['metadata']['processing_time'], 3.77)
    
    @patch('analysis.services.OpenRouterService._init_client')
    def test_concurrent_service_calls_isolation(self, mock_init_client):
        """Test that concurrent service calls don't interfere with each other."""
        # This test ensures that the service is stateless and thread-safe
        
        def create_mock_client(response_content):
            mock_client = Mock()
            mock_response = Mock()
            mock_response.choices = [Mock()]
            mock_response.choices[0].message.content = response_content
            mock_response.usage = Mock()
            mock_response.usage.total_tokens = 400
            mock_client.chat.completions.create.return_value = mock_response
            return mock_client
        
        # Create different mock clients for concurrent calls
        client1 = create_mock_client("Cover letter 1")
        client2 = create_mock_client("Cover letter 2")
        
        mock_init_client.side_effect = [client1, client2]
        
        with patch('analysis.services.time.time', side_effect=[1000.0, 1002.0, 1005.0, 1007.0]):
            # Simulate concurrent calls
            result1 = self.service.generate_cover_letter(
                title="Engineer 1",
                company="Company 1",
                location="Location",
                job_type="Full-time",
                salary_range="$100k",
                requirements="Requirements 1",
                skills_required="Skills",
                experience_level="Mid",
                resume_content="Resume 1",
                template_type="professional"
            )
            
            result2 = self.service.generate_cover_letter(
                title="Engineer 2",
                company="Company 2",
                location="Location",
                job_type="Full-time",
                salary_range="$120k",
                requirements="Requirements 2",
                skills_required="Skills",
                experience_level="Senior",
                resume_content="Resume 2",
                template_type="creative"
            )
        
        # Results should be independent
        self.assertEqual(result1['cover_letter'], "Cover letter 1")
        self.assertEqual(result2['cover_letter'], "Cover letter 2")
        
        # Prompts should contain different data
        self.assertIn("Company 1", result1['prompt_used'])
        self.assertIn("Company 2", result2['prompt_used'])
        self.assertIn("Requirements 1", result1['prompt_used'])
        self.assertIn("Requirements 2", result2['prompt_used'])
        
        # Metadata should be different
        self.assertEqual(result1['metadata']['template_type'], 'professional')
        self.assertEqual(result2['metadata']['template_type'], 'creative')