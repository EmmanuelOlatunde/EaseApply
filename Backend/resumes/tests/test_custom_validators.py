"""
Tests for custom validators and utility functions
"""

from django.test import TestCase
from django.core.files.uploadedfile import SimpleUploadedFile
from ..utils import (
    validate_resume_file,
    extract_full_name,
    extract_contact_info,
    extract_summary,
    extract_skills,
    extract_work_experience,
    extract_education,
    parse_resume_content
)


class ResumeValidationTestCase(TestCase):
    """Test custom validation functions"""
    
    def test_validate_resume_file_edge_cases(self):
        """Test file validation edge cases"""
        # Test None file
        file_type, is_valid = validate_resume_file(None)
        self.assertEqual(file_type, '')
        self.assertFalse(is_valid)
        
        # Test file at exact size limit (10MB)
        exact_limit_content = b'x' * (10 * 1024 * 1024)  # Exactly 10MB
        exact_limit_file = SimpleUploadedFile(
            "exact_limit.pdf",
            exact_limit_content,
            content_type="application/pdf"
        )
        
        file_type, is_valid = validate_resume_file(exact_limit_file)
        self.assertEqual(file_type, 'pdf')
        self.assertFalse(is_valid)  # Should be false as it equals the limit
        
        # Test file just under limit
        under_limit_content = b'x' * (10 * 1024 * 1024 - 1)  # Just under 10MB
        under_limit_file = SimpleUploadedFile(
            "under_limit.pdf",
            under_limit_content,
            content_type="application/pdf"
        )
        
        file_type, is_valid = validate_resume_file(under_limit_file)
        self.assertEqual(file_type, 'pdf')
        self.assertTrue(is_valid)
    
    def test_file_extension_case_sensitivity(self):
        """Test file extension validation with different cases"""
        test_cases = [
            ("resume.PDF", "pdf", True),
            ("resume.Pdf", "pdf", True),
            ("resume.DOCX", "docx", True),
            ("resume.DocX", "docx", True),
            ("resume.DOC", "docx", True),
        ]
        
        for filename, expected_type, expected_valid in test_cases:
            file = SimpleUploadedFile(
                filename,
                b'fake content',
                content_type="application/octet-stream"
            )
            
            file_type, is_valid = validate_resume_file(file)
            self.assertEqual(file_type, expected_type)
            self.assertEqual(is_valid, expected_valid)


class ResumeParsingTestCase(TestCase):
    """Test resume content parsing functions"""
    
    def test_extract_full_name_variations(self):
        """Test full name extraction with various formats"""
        test_cases = [
            ("John Doe\nSoftware Engineer", "John Doe"),
            ("JANE SMITH\nProject Manager", "JANE SMITH"),
            ("Dr. Michael Johnson\nSenior Developer", "Dr. Michael Johnson"),
            ("  Mary Williams  \nData Scientist", "Mary Williams"),
            ("Summary\nExperienced developer", None),  # Should skip summary lines
            ("123 Main St\nJohn Adams", "John Adams"),  # Should skip address-like lines
            ("", None),  # Empty text
            ("J\nSoftware Engineer", None),  # Too short
        ]
        
        for text, expected in test_cases:
            result = extract_full_name(text)
            self.assertEqual(result, expected)
    
    def test_extract_contact_info_comprehensive(self):
        """Test comprehensive contact information extraction"""
        test_text = """
        John Doe
        Senior Software Engineer
        Email: john.doe@company.com
        Phone: +1 (555) 123-4567
        LinkedIn: https://linkedin.com/in/johndoe
        GitHub: github.com/johndoe
        Address: 123 Main Street, City, State 12345
        """
        
        contact_info = extract_contact_info(test_text)
        
        self.assertEqual(contact_info['email'], 'john.doe@company.com')
        self.assertEqual(contact_info['phone'], '+1 (555) 123-4567')
        self.assertEqual(contact_info['linkedin'], 'https://linkedin.com/in/johndoe')
        self.assertEqual(contact_info['github'], 'github.com/johndoe')
        self.assertIn('12345', contact_info['address'])
    
    def test_extract_contact_info_edge_cases(self):
        """Test contact info extraction edge cases"""
        # Multiple emails - should get the first one
        multi_email_text = "Contact: john@work.com or personal: john@personal.com"
        contact_info = extract_contact_info(multi_email_text)
        self.assertEqual(contact_info['email'], 'john@work.com')
        
        # Various phone formats
        phone_formats = [
            ("Call me at 555-123-4567", "555-123-4567"),
            ("Phone: (555) 123-4567", "(555) 123-4567"),
            ("Mobile: +1-555-123-4567", "+1-555-123-4567"),
            ("Tel: 555.123.4567", "555.123.4567"),
        ]
        
        for text, expected_phone in phone_formats:
            contact_info = extract_contact_info(text)
            self.assertEqual(contact_info['phone'], expected_phone)
    
    def test_extract_summary_variations(self):
        """Test summary extraction with different formats"""
        test_cases = [
            (
                "SUMMARY\nExperienced software engineer with 5+ years\n\nEXPERIENCE\nDeveloper at Tech Corp",
                "Experienced software engineer with 5+ years"
            ),
            (
                "Professional Summary:\nPassionate developer with expertise in Python\nand web technologies\n\nSkills:\nPython, Django",
                "Passionate developer with expertise in Python and web technologies"
            ),
            (
                "OBJECTIVE\nSeeking a challenging role in software development\n\nEducation\nBS Computer Science",
                "Seeking a challenging role in software development"
            ),
            (
                "Experience\nDeveloper at Tech Corp\nEducation\nBS Degree",
                None  # No summary section
            ),
        ]
        
        for text, expected in test_cases:
            result = extract_summary(text)
            self.assertEqual(result, expected)
    
    def test_extract_skills_comprehensive(self):
        """Test comprehensive skills extraction"""
        test_text = """
        SKILLS
        Programming Languages: Python, JavaScript, Java
        Frameworks: Django, React, Spring Boot
        Databases: PostgreSQL, MongoDB
        Tools: Git, Docker, Jenkins
        
        TECHNICAL SKILLS
        • Machine Learning
        • Data Analysis
        • Cloud Computing (AWS, Azure)
        
        Core Competencies: Leadership, Communication, Problem Solving
        """
        
        skills = extract_skills(test_text)
        
        # Should extract skills from various formats
        self.assertIn('Python', skills)
        self.assertIn('JavaScript', skills)
        self.assertIn('Django', skills)
        self.assertIn('Machine Learning', skills)
        self.assertIn('Leadership', skills)
    
    def test_extract_work_experience_complex(self):
        """Test work experience extraction with complex formatting"""
        test_text = """
        WORK EXPERIENCE
        
        Senior Software Engineer | Tech Solutions Inc | 2020-2023
        • Led development of microservices architecture
        • Mentored junior developers
        • Improved system performance by 40%
        
        Software Developer | StartupCorp | 2018-2020
        • Developed web applications using React and Node.js
        • Collaborated with cross-functional teams
        
        Junior Developer | First Company | 2016-2018
        """
        
        experience = extract_work_experience(test_text)
        
        self.assertGreater(len(experience), 0)
        # Note: The exact parsing logic may vary based on implementation
        # This test verifies that the function processes the input without errors
    
    def test_extract_education_formats(self):
        """Test education extraction with different formats"""
        test_cases = [
            """
            EDUCATION
            Bachelor of Science in Computer Science | University of Technology | 2016
            Master of Science in Software Engineering | Tech University | 2018
            """,
            """
            ACADEMIC BACKGROUND
            BS Computer Science, State University, 2015
            MS Data Science, Tech Institute, 2017
            """,
        ]
        
        for text in test_cases:
            education = extract_education(text)
            self.assertGreater(len(education), 0)
    
    def test_parse_resume_content_integration(self):
        """Test complete resume content parsing integration"""
        comprehensive_resume = """
        John Smith
        Senior Software Engineer
        
        Email: john.smith@email.com
        Phone: (555) 123-4567
        LinkedIn: linkedin.com/in/johnsmith
        
        PROFESSIONAL SUMMARY
        Experienced software engineer with 8+ years of experience in full-stack development.
        Passionate about creating scalable solutions and mentoring junior developers.
        
        TECHNICAL SKILLS
        Languages: Python, JavaScript, Java, C++
        Frameworks: Django, React, Spring Boot, Express.js
        Databases: PostgreSQL, MongoDB, Redis
        Cloud: AWS, Docker, Kubernetes
        
        PROFESSIONAL EXPERIENCE
        Senior Software Engineer | TechCorp Inc | 2019-2023
        • Led development of microservices architecture serving 1M+ users
        • Implemented CI/CD pipelines reducing deployment time by 60%
        • Mentored 5 junior developers and conducted code reviews
        
        Software Engineer | StartupTech | 2016-2019
        • Developed full-stack web applications using React and Django
        • Collaborated with product team to define technical requirements
        • Optimized database queries improving performance by 35%
        
        EDUCATION
        Master of Science in Computer Science | Tech University | 2016
        Bachelor of Science in Software Engineering | State College | 2014
        
        CERTIFICATIONS
        AWS Certified Solutions Architect
        Certified Kubernetes Administrator
        
        PROJECTS
        E-commerce Platform
        • Built scalable e-commerce platform using Django and React
        • Implemented payment processing and inventory management
        
        Data Analytics Dashboard
        • Created real-time dashboard for business metrics
        • Used Python, PostgreSQL, and D3.js for visualization
        """
        
        parsed_data = parse_resume_content(comprehensive_resume)
        
        # Verify all sections are parsed
        self.assertEqual(parsed_data['fullName'], 'John Smith')
        self.assertIn('Experienced software engineer', parsed_data['summary'])
        self.assertEqual(parsed_data['contactInfo']['email'], 'john.smith@email.com')
        self.assertIn('Python', parsed_data['skills'])
        self.assertGreater(len(parsed_data['workExperience']), 0)
        self.assertGreater(len(parsed_data['education']), 0)
        self.assertIn('AWS Certified Solutions Architect', parsed_data['certifications'])
        self.assertGreater(len(parsed_data['projects']), 0)


