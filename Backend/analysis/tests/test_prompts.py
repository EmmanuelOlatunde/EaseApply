"""
Test suite for Analysis app prompt templates.
Tests prompt generation, formatting, and template variations.
"""

from analysis.prompts import CoverLetterPrompts
from .test_base import BaseAnalysisTestCase


class CoverLetterPromptsTest(BaseAnalysisTestCase):
    """Test suite for CoverLetterPrompts class."""
    
    def setUp(self):
        super().setUp()
        self.sample_job_data = {
            'title': 'Senior Software Engineer',
            'company': 'Tech Innovations Inc.',
            'location': 'San Francisco, CA',
            'job_type': 'Full-time',
            'salary_range': '$130,000 - $160,000',
            'requirements': 'Bachelor\'s degree in Computer Science, 5+ years experience with Python, Django, and REST APIs. Experience with cloud platforms (AWS/GCP) preferred.',
            'skills_required': 'Python, Django, PostgreSQL, AWS, Docker, Kubernetes, Git',
            'experience_level': 'Senior'
        }
        
        self.sample_resume_content = """
        John Smith
        Senior Software Engineer
        john.smith@email.com | (555) 123-4567
        
        EXPERIENCE:
        Senior Software Engineer - DataCorp (2020-2024)
        • Led development of microservices architecture serving 2M+ daily active users
        • Implemented CI/CD pipelines reducing deployment time by 60%
        • Mentored team of 8 junior developers
        • Built REST APIs using Django and PostgreSQL
        • Managed AWS infrastructure with Docker and Kubernetes
        
        Software Engineer - StartupXYZ (2018-2020)
        • Developed full-stack web applications using Python and React
        • Optimized database queries improving performance by 40%
        • Collaborated with cross-functional teams in Agile environment
        
        EDUCATION:
        B.S. Computer Science - Stanford University (2018)
        
        SKILLS:
        Python, Django, JavaScript, React, PostgreSQL, MongoDB, AWS, Docker, Kubernetes, Git
        """
    
    def test_get_professional_prompt_template(self):
        """Test retrieving professional prompt template."""
        prompt = CoverLetterPrompts.get_prompt('professional')
        
        self.assertIsInstance(prompt, str)
        self.assertIn('expert cover letter writer', prompt.lower())
        self.assertIn('4-paragraph professional cover letter', prompt)
        self.assertIn('ATS-optimized', prompt)
        self.assertIn('350–500 words', prompt)
        self.assertIn('{title}', prompt)
        self.assertIn('{company}', prompt)
        self.assertIn('{resume_content}', prompt)
    
    def test_get_creative_prompt_template(self):
        """Test retrieving creative prompt template."""
        prompt = CoverLetterPrompts.get_prompt('creative')
        
        self.assertIsInstance(prompt, str)
        self.assertIn('creative cover letter expert', prompt.lower())
        self.assertIn('story-driven', prompt)
        self.assertIn('personality-rich', prompt)
        self.assertIn('creative call to action', prompt)
        self.assertIn('350–500 words', prompt)
        self.assertIn('{title}', prompt)
        self.assertIn('{resume_content}', prompt)
    
    def test_get_default_prompt_template(self):
        """Test that default template returns professional when no type specified."""
        default_prompt = CoverLetterPrompts.get_prompt()
        professional_prompt = CoverLetterPrompts.get_prompt('professional')
        
        self.assertEqual(default_prompt, professional_prompt)
    
    def test_get_invalid_prompt_template_returns_default(self):
        """Test that invalid template type returns professional template."""
        invalid_prompt = CoverLetterPrompts.get_prompt('invalid_type')
        professional_prompt = CoverLetterPrompts.get_prompt('professional')
        
        self.assertEqual(invalid_prompt, professional_prompt)
    
    def test_professional_prompt_formatting(self):
        """Test formatting professional prompt with job and resume data."""
        prompt_template = CoverLetterPrompts.get_prompt('professional')
        
        formatted_prompt = prompt_template.format(
            **self.sample_job_data,
            resume_content=self.sample_resume_content
        )
        
        # Verify all placeholders are replaced
        self.assertNotIn('{', formatted_prompt)
        self.assertNotIn('}', formatted_prompt)
        
        # Verify job data is included
        self.assertIn('Senior Software Engineer', formatted_prompt)
        self.assertIn('Tech Innovations Inc.', formatted_prompt)
        self.assertIn('San Francisco, CA', formatted_prompt)
        self.assertIn('Full-time', formatted_prompt)
        self.assertIn('$130,000 - $160,000', formatted_prompt)
        self.assertIn('Bachelor\'s degree in Computer Science', formatted_prompt)
        self.assertIn('Python, Django, PostgreSQL', formatted_prompt)
        self.assertIn('Senior', formatted_prompt)
        
        # Verify resume content is included
        self.assertIn('John Smith', formatted_prompt)
        self.assertIn('DataCorp', formatted_prompt)
        self.assertIn('2M+ daily active users', formatted_prompt)
        self.assertIn('Stanford University', formatted_prompt)
    
    def test_creative_prompt_formatting(self):
        """Test formatting creative prompt with job and resume data."""
        prompt_template = CoverLetterPrompts.get_prompt('creative')
        
        # Creative template expects job_description as a combined field
        f"""
        Job title = {self.sample_job_data['title']},
        company name = {self.sample_job_data['company']},
        location = {self.sample_job_data['location']},
        job_type = {self.sample_job_data['job_type']},
        salary_range = {self.sample_job_data['salary_range']},
        requirements = {self.sample_job_data['requirements']},
        skills_required = {self.sample_job_data['skills_required']},
        experience_level = {self.sample_job_data['experience_level']}
        """
        
        formatted_prompt = prompt_template.format(
            title=self.sample_job_data['title'],
            company=self.sample_job_data['company'],
            location=self.sample_job_data['location'],
            job_type=self.sample_job_data['job_type'],
            salary_range=self.sample_job_data['salary_range'],
            requirements=self.sample_job_data['requirements'],
            skills_required=self.sample_job_data['skills_required'],
            experience_level=self.sample_job_data['experience_level'],
            resume_content=self.sample_resume_content
        )
                
        # Verify placeholders are replaced
        self.assertNotIn('{job_description}', formatted_prompt)
        self.assertNotIn('{resume_content}', formatted_prompt)
        
        # Verify content is included
        self.assertIn('Senior Software Engineer', formatted_prompt)
        self.assertIn('Tech Innovations Inc.', formatted_prompt)
        self.assertIn('John Smith', formatted_prompt)
    
    def test_prompt_contains_required_instructions(self):
        """Test that prompts contain all required instructions for AI."""
        professional_prompt = CoverLetterPrompts.get_prompt('professional')
        
        # Check for key instruction elements
        required_elements = [
            'Job Description:',
            'Candidate Resume:',
            'Instructions:',
            'Constraints:',
            'Word count:',
            'No placeholders',
            'ready-to-use',
            'sign-off',
            'candidate\'s full name'
        ]
        
        for element in required_elements:
            self.assertIn(element, professional_prompt)
    
    def test_creative_prompt_contains_creative_instructions(self):
        """Test that creative prompt contains creativity-specific instructions."""
        creative_prompt = CoverLetterPrompts.get_prompt('creative')
        
        creative_elements = [
            'story-driven',
            'personality-rich',
            'bold hook',
            'storytelling',
            'creative call to action',
            'Avoid generic openings',
            'STAR method'
        ]
        
        for element in creative_elements:
            self.assertIn(element, creative_prompt)
    
    def test_prompt_word_count_constraints(self):
        """Test that prompts specify appropriate word count constraints."""
        professional_prompt = CoverLetterPrompts.get_prompt('professional')
        creative_prompt = CoverLetterPrompts.get_prompt('creative')
        
        # Both should have word count constraints
        self.assertIn('350–500 words', professional_prompt)
        self.assertIn('350–500 words', creative_prompt)
    
    def test_prompt_quality_guidelines(self):
        """Test that prompts include quality and authenticity guidelines."""
        professional_prompt = CoverLetterPrompts.get_prompt('professional')
        
        quality_guidelines = [
            'Only resume evidence', 
            'dont falsify any information',
            'quantified where possible',
            'natural, simple words and gramatical',
            'No placeholders or incomplete letters'
        ]
        
        for guideline in quality_guidelines:
            self.assertIn(guideline, professional_prompt)
    
    def test_prompts_dictionary_completeness(self):
        """Test that PROMPTS dictionary contains expected templates."""
        prompts_dict = CoverLetterPrompts.PROMPTS
        
        # Check that expected templates exist
        expected_templates = ['professional', 'creative']
        
        for template in expected_templates:
            self.assertIn(template, prompts_dict)
            self.assertIsInstance(prompts_dict[template], str)
            self.assertTrue(len(prompts_dict[template]) > 100)  # Non-empty templates
    
    def test_prompt_template_structure_consistency(self):
        """Test that all prompt templates have consistent structure."""
        for template_name, template in CoverLetterPrompts.PROMPTS.items():
            with self.subTest(template=template_name):
                # All templates should have these sections
                self.assertIn('Instructions:', template)
                self.assertIn('Constraints:', template)
                self.assertIn('Word count:', template)
                
                # All templates should specify output requirements
                self.assertIn('ready-to-use', template)
                self.assertIn('human-like language', template)
    
    def test_prompt_placeholders_consistency(self):
        """Test that prompt placeholders are consistent with expected format."""
        professional_prompt = CoverLetterPrompts.get_prompt('professional')
        
        # Professional template should have individual job field placeholders
        job_placeholders = [
            '{title}', '{company}', '{location}', '{job_type}',
            '{salary_range}', '{requirements}', '{skills_required}',
            '{experience_level}', '{resume_content}'
        ]
        
        for placeholder in job_placeholders:
            self.assertIn(placeholder, professional_prompt)
    
    def test_prompt_formatting_with_special_characters(self):
        """Test prompt formatting with special characters in data."""
        prompt_template = CoverLetterPrompts.get_prompt('professional')
        
        special_char_data = {
            'title': 'Software Engineer & Data Scientist',
            'company': 'Tech Corp "The Best"',
            'location': 'San Francisco, CA (Remote OK)',
            'job_type': 'Full-time/Contract',
            'salary_range': '$100k-$150k + equity',
            'requirements': 'Requirements with "quotes" and <tags>',
            'skills_required': 'Python/Django, AWS/GCP, CI/CD',
            'experience_level': 'Mid-Senior',
            'resume_content': 'Resume with special chars: & < > " \' / \\'
        }
        
        # Should not raise an error
        formatted_prompt = prompt_template.format(**special_char_data)
        
        # Special characters should be preserved
        self.assertIn('Software Engineer & Data Scientist', formatted_prompt)
        self.assertIn('Tech Corp "The Best"', formatted_prompt)
        self.assertIn('Python/Django', formatted_prompt)
    
    def test_prompt_formatting_with_empty_fields(self):
        """Test prompt formatting with empty field values."""
        prompt_template = CoverLetterPrompts.get_prompt('professional')
        
        empty_data = {
            'title': '',
            'company': '',
            'location': '',
            'job_type': '',
            'salary_range': '',
            'requirements': '',
            'skills_required': '',
            'experience_level': '',
            'resume_content': ''
        }
        
        # Should not raise an error with empty values
        formatted_prompt = prompt_template.format(**empty_data)
        
        # Should still be a valid prompt structure
        self.assertIn('Job Description:', formatted_prompt)
        self.assertIn('Candidate Resume:', formatted_prompt)