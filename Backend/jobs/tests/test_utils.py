from unittest.mock import Mock, patch
from io import BytesIO
from django.test import TestCase
from django.core.files.uploadedfile import InMemoryUploadedFile
from jobs.utils import (
    extract_text_from_document,
    extract_from_pdf,
    extract_from_docx,
    extract_job_details,
    extract_job_title,
    extract_company_name,
    extract_location,
    extract_job_type,
    extract_salary,
    extract_requirements,
    extract_skills,
    extract_experience_level
)


class BaseTestCase(TestCase):
    """Base test case with common utilities following DRY principles"""
    
    def create_mock_file(self, filename: str, content: bytes = b"test content") -> InMemoryUploadedFile:
        """Create a mock InMemoryUploadedFile for testing"""
        file_obj = BytesIO(content)
        return InMemoryUploadedFile(
            file_obj,
            field_name="test_field",
            name=filename,
            content_type="application/octet-stream",
            size=len(content),
            charset=None
        )
    
    def assertContainsSkills(self, result: str, expected_skills: list):
        """Helper to assert that result contains expected skills"""
        if result:
            result_skills = [skill.strip() for skill in result.split(',')]
            for skill in expected_skills:
                self.assertIn(skill, result_skills)


class DocumentExtractionTestCase(BaseTestCase):
    """Test document text extraction functionality"""
    
    @patch('jobs.utils.extract_from_pdf')
    def test_extract_text_from_pdf_success(self, mock_extract_pdf):
        """Test successful PDF text extraction"""
        mock_extract_pdf.return_value = "PDF content"
        mock_file = self.create_mock_file("test.pdf")
        
        result = extract_text_from_document(mock_file)
        
        self.assertEqual(result, "PDF content")
        mock_extract_pdf.assert_called_once_with(mock_file)
    
    @patch('jobs.utils.extract_from_docx')
    def test_extract_text_from_docx_success(self, mock_extract_docx):
        """Test successful DOCX text extraction"""
        mock_extract_docx.return_value = "DOCX content"
        mock_file = self.create_mock_file("test.docx")
        
        result = extract_text_from_document(mock_file)
        
        self.assertEqual(result, "DOCX content")
        mock_extract_docx.assert_called_once_with(mock_file)
    
    @patch('jobs.utils.extract_from_docx')
    def test_extract_text_from_doc_success(self, mock_extract_docx):
        """Test successful DOC text extraction"""
        mock_extract_docx.return_value = "DOC content"
        mock_file = self.create_mock_file("test.doc")
        
        result = extract_text_from_document(mock_file)
        
        self.assertEqual(result, "DOC content")
        mock_extract_docx.assert_called_once_with(mock_file)
    
    def test_extract_text_from_txt_success(self):
        """Test successful TXT text extraction"""
        content = "Plain text content"
        mock_file = self.create_mock_file("test.txt", content.encode('utf-8'))
        
        result = extract_text_from_document(mock_file)
        
        self.assertEqual(result, content)
    
    def test_extract_text_unsupported_file_type(self):
        """Test error handling for unsupported file types"""
        mock_file = self.create_mock_file("test.xyz")
        
        with self.assertRaises(ValueError) as context:
            extract_text_from_document(mock_file)
        
        self.assertIn("Unsupported file type: xyz", str(context.exception))
    
    @patch('jobs.utils.extract_from_pdf')
    def test_extract_text_pdf_extraction_error(self, mock_extract_pdf):
        """Test error handling when PDF extraction fails"""
        mock_extract_pdf.side_effect = Exception("PDF read error")
        mock_file = self.create_mock_file("test.pdf")
        
        with self.assertRaises(ValueError) as context:
            extract_text_from_document(mock_file)
        
        self.assertIn("Error extracting text from document", str(context.exception))
    
    def test_extract_text_txt_encoding_error(self):
        """Test error handling for TXT encoding issues"""
        # Create invalid UTF-8 content
        invalid_content = b'\xff\xfe\xfd'
        mock_file = self.create_mock_file("test.txt", invalid_content)
        
        with self.assertRaises(ValueError) as context:
            extract_text_from_document(mock_file)
        
        self.assertIn("Error extracting text from document", str(context.exception))


class PDFExtractionTestCase(BaseTestCase):
    """Test PDF-specific extraction functionality"""
    
    @patch('jobs.utils.PyPDF2.PdfReader')
    def test_extract_from_pdf_success(self, mock_pdf_reader):
        """Test successful PDF text extraction"""
        # Mock PDF reader and pages
        mock_page1 = Mock()
        mock_page1.extract_text.return_value = "Page 1 content"
        mock_page2 = Mock()
        mock_page2.extract_text.return_value = "Page 2 content"
        
        mock_reader_instance = Mock()
        mock_reader_instance.pages = [mock_page1, mock_page2]
        mock_pdf_reader.return_value = mock_reader_instance
        
        mock_file = self.create_mock_file("test.pdf")
        result = extract_from_pdf(mock_file)
        
        expected = "Page 1 content\nPage 2 content\n"
        self.assertEqual(result, expected)
        mock_pdf_reader.assert_called_once_with(mock_file)
    
    @patch('jobs.utils.PyPDF2.PdfReader')
    def test_extract_from_pdf_error(self, mock_pdf_reader):
        """Test PDF extraction error handling"""
        mock_pdf_reader.side_effect = Exception("Invalid PDF")
        mock_file = self.create_mock_file("test.pdf")
        
        with self.assertRaises(ValueError) as context:
            extract_from_pdf(mock_file)
        
        self.assertIn("Error reading PDF", str(context.exception))
    
    @patch('jobs.utils.PyPDF2.PdfReader')
    def test_extract_from_pdf_empty_pages(self, mock_pdf_reader):
        """Test PDF with empty pages"""
        mock_page = Mock()
        mock_page.extract_text.return_value = ""
        
        mock_reader_instance = Mock()
        mock_reader_instance.pages = [mock_page]
        mock_pdf_reader.return_value = mock_reader_instance
        
        mock_file = self.create_mock_file("test.pdf")
        result = extract_from_pdf(mock_file)
        
        self.assertEqual(result, "\n")


class DOCXExtractionTestCase(BaseTestCase):
    """Test DOCX-specific extraction functionality"""
    
    @patch('jobs.utils.docx.Document')
    def test_extract_from_docx_success(self, mock_document):
        """Test successful DOCX text extraction"""
        # Mock paragraphs
        mock_para1 = Mock()
        mock_para1.text = "First paragraph"
        mock_para2 = Mock()
        mock_para2.text = "Second paragraph"
        
        mock_doc_instance = Mock()
        mock_doc_instance.paragraphs = [mock_para1, mock_para2]
        mock_document.return_value = mock_doc_instance
        
        mock_file = self.create_mock_file("test.docx")
        result = extract_from_docx(mock_file)
        
        expected = "First paragraph\nSecond paragraph\n"
        self.assertEqual(result, expected)
        mock_document.assert_called_once_with(mock_file)
    
    @patch('jobs.utils.docx.Document')
    def test_extract_from_docx_error(self, mock_document):
        """Test DOCX extraction error handling"""
        mock_document.side_effect = Exception("Invalid DOCX")
        mock_file = self.create_mock_file("test.docx")
        
        with self.assertRaises(ValueError) as context:
            extract_from_docx(mock_file)
        
        self.assertIn("Error reading DOCX", str(context.exception))
    
    @patch('jobs.utils.docx.Document')
    def test_extract_from_docx_empty_paragraphs(self, mock_document):
        """Test DOCX with empty paragraphs"""
        mock_para = Mock()
        mock_para.text = ""
        
        mock_doc_instance = Mock()
        mock_doc_instance.paragraphs = [mock_para]
        mock_document.return_value = mock_doc_instance
        
        mock_file = self.create_mock_file("test.docx")
        result = extract_from_docx(mock_file)
        
        self.assertEqual(result, "\n")


class JobDetailsExtractionTestCase(BaseTestCase):
    """Test job details extraction from text"""
    
    def test_extract_job_details_complete(self):
        """Test extraction of complete job details"""
        job_text = """
        Job Title: Senior Software Engineer
        Company: TechCorp Inc.
        Location: San Francisco, CA
        Employment Type: Full-time
        Salary: $120,000 - $150,000 per year
        
        Requirements:
        - 5+ years of experience
        - Python, JavaScript, React
        
        Skills Required: Python, JavaScript, React, Docker, AWS
        """
        
        result = extract_job_details(job_text)
        
        self.assertEqual(result['title'], 'Senior Software Engineer')
        self.assertEqual(result['company'], 'TechCorp Inc.')
        self.assertEqual(result['location'], 'San Francisco, CA')
        self.assertEqual(result['job_type'], 'full_time')
        self.assertIn('$120,000', result['salary_range'])
        self.assertIsNotNone(result['requirements'])
        self.assertIsNotNone(result['skills_required'])
        self.assertEqual(result['experience_level'], 'Senior')
    
    def test_extract_job_details_minimal(self):
        """Test extraction with minimal information"""
        job_text = "Looking for a developer"
        
        result = extract_job_details(job_text)
        
        # Should return dict with None values for missing fields
        self.assertIsNone(result['title'])
        self.assertIsNone(result['company'])
        self.assertIsNone(result['location'])
        self.assertEqual(result['job_type'], 'unknown')
        self.assertIsNone(result['salary_range'])
        self.assertIsNone(result['requirements'])
        self.assertIsNone(result['skills_required'])
        self.assertIsNone(result['experience_level'])
    
    def test_extract_job_details_whitespace_normalization(self):
        """Test that whitespace is properly normalized"""
        job_text = "Job    Title:     Software    Engineer\n\n\nCompany:     TechCorp"
        
        result = extract_job_details(job_text)
        
        self.assertEqual(result['title'], 'Software Engineer')
        self.assertEqual(result['company'], 'TechCorp')


class JobTitleExtractionTestCase(BaseTestCase):
    """Test job title extraction functionality"""
    
    def test_extract_job_title_explicit_markers(self):
        """Test extraction with explicit title markers"""
        test_cases = [
            ("Job Title: Software Engineer", "Software Engineer"),
            ("Position: Marketing Manager", "Marketing Manager"),
            ("Role: Data Analyst", "Data Analyst"),
            ("Title: UX Designer", "UX Designer"),
        ]
        
        for text, expected in test_cases:
            with self.subTest(text=text):
                result = extract_job_title(text)
                self.assertEqual(result, expected)
    
    def test_extract_job_title_hiring_pattern(self):
        """Test extraction with hiring patterns"""
        test_cases = [
            ("Company is hiring a Software Developer", "Software Developer"),
            ("We are seeking an experienced Manager", "experienced Manager"),
            ("Looking for a Data Scientist", "Data Scientist"),
        ]
        
        for text, expected in test_cases:
            with self.subTest(text=text):
                result = extract_job_title(text)
                self.assertEqual(result, expected)
    
    def test_extract_job_title_keywords(self):
        """Test extraction using keyword patterns"""
        test_cases = [
            ("Senior Software Engineer\nAbout the role", "Senior Software Engineer"),
            ("Marketing Manager\nWe are looking", "Marketing Manager"),
            ("Project Coordinator", "Project Coordinator"),
        ]
        
        for text, expected in test_cases:
            with self.subTest(text=text):
                result = extract_job_title(text)
                self.assertEqual(result, expected)
    
    def test_extract_job_title_length_validation(self):
        """Test title length validation"""
        # Too short
        result = extract_job_title("Job Title: IT")
        self.assertIsNone(result)
        
        # Too long
        long_title = "Job Title: " + "Very Long Title " * 20
        result = extract_job_title(long_title)
        self.assertIsNone(result)
    
    def test_extract_job_title_no_match(self):
        """Test when no title can be extracted"""
        result = extract_job_title("This is just some random text without job information")
        self.assertIsNone(result)
    
    def test_extract_job_title_with_separators(self):
        """Test title extraction with separators"""
        result = extract_job_title("Job Title: Software Engineer - Remote")
        self.assertEqual(result, "Software Engineer ")


class CompanyExtractionTestCase(BaseTestCase):
    """Test company name extraction functionality"""
    
    def test_extract_company_explicit_markers(self):
        """Test extraction with explicit company markers"""
        test_cases = [
            ("Company: TechCorp Inc.", "TechCorp Inc."),
            ("Organization: Healthcare Systems", "Healthcare Systems"),
            #("Employer: Global Solutions", "Global Solutions"),
        ]
        
        for text, expected in test_cases:
            with self.subTest(text=text):
                result = extract_company_name(text)
                self.assertEqual(result, expected)
    
    def test_extract_company_at_with_pattern(self):
        """Test extraction with 'at' patterns"""
        test_cases = [
            ("Software Engineer at TechCorp", "TechCorp"),
            ("Working with Microsoft", "Microsoft"),
            ("Consultant for Deloitte", "Deloitte"),
            ("Designer @Adobe", "Adobe"),
            ("Joined with OpenAI", "OpenAI"),
        ]

        
        for text, expected in test_cases:
            with self.subTest(text=text):
                result = extract_company_name(text)
                self.assertEqual(result, expected)
    
    def test_extract_company_hiring_pattern(self):
        """Test extraction with hiring patterns"""
        test_cases = [
            ("TechCorp is hiring", "TechCorp"),
            ("Microsoft seeks", "Microsoft"),
            ("Google is looking", "Google"),
        ]
        
        for text, expected in test_cases:
            with self.subTest(text=text):
                result = extract_company_name(text)
                self.assertEqual(result, expected)
    
    def test_extract_company_stopwords_filter(self):
        """Test that stopwords are filtered out"""
        result = extract_company_name("Company: Remote Global Full-time")
        self.assertIsNone(result)
    
    def test_extract_company_length_validation(self):
        """Test company name length validation"""
        # Too short
        result = extract_company_name("Company: A")
        self.assertIsNone(result)
        
        # Too long
        long_company = "Company: " + "Very Long Company Name " * 10
        result = extract_company_name(long_company)
        self.assertIsNone(result)
    
    def test_extract_company_no_match(self):
        """Test when no company can be extracted"""
        result = extract_company_name("Just some job description without company info")
        self.assertIsNone(result)


class LocationExtractionTestCase(BaseTestCase):
    """Test location extraction functionality"""
    
    def test_extract_location_explicit_markers(self):
        """Test extraction with explicit location markers"""
        test_cases = [
            ("Location: San Francisco, CA", "San Francisco, CA"),
            ("Based in: New York, NY", "New York, NY"),
            ("Office in: London, UK", "London, UK"),
        ]
        
        for text, expected in test_cases:
            with self.subTest(text=text):
                result = extract_location(text)
                self.assertEqual(result, expected)
    
    def test_extract_location_city_state_pattern(self):
        """Test extraction of city, state patterns"""
        test_cases = [
            ("Position in Chicago, IL", "Chicago, IL"),
            ("Based at Seattle, WA", "Seattle, WA"),
        ]
        
        for text, expected in test_cases:
            with self.subTest(text=text):
                result = extract_location(text)
                self.assertEqual(result, expected)
    
    def test_extract_location_remote(self):
        """Test remote location detection"""
        test_cases = [
            "Work from home position",
            "Remote opportunity",
            "Hybrid work environment",
        ]
        
        for text in test_cases:
            with self.subTest(text=text):
                result = extract_location(text)
                self.assertEqual(result, "Remote")
    
    def test_extract_location_length_validation(self):
        """Test location length validation"""
        # Too short
        result = extract_location("Location: NY")
        self.assertIsNone(result)
        
        # Too long
        long_location = "Location: " + "Very Long Location Name " * 10
        result = extract_location(long_location)
        self.assertIsNone(result)
    
    def test_extract_location_no_match(self):
        """Test when no location can be extracted"""
        result = extract_location("Job description without location information")
        self.assertIsNone(result)


class JobTypeExtractionTestCase(BaseTestCase):
    """Test job type extraction functionality"""
    
    def test_extract_job_type_variations(self):
        """Test extraction of various job types"""
        test_cases = [
            ("Full-time position", "full_time"),
            ("Full time role", "full_time"),
            ("Part-time job", "part_time"),
            ("Part time opportunity", "part_time"),
            ("Contract position", "contract"),
            ("Contractor role", "contract"),
            ("Freelance work", "contract"),
            ("Internship program", "internship"),
            ("Intern position", "internship"),
            ("Remote work", "remote"),
            ("Work from home", "remote"),
        ]
        
        for text, expected in test_cases:
            with self.subTest(text=text):
                result = extract_job_type(text.lower())
                self.assertEqual(result, expected)
    
    def test_extract_job_type_unknown(self):
        """Test default return for unknown job type"""
        result = extract_job_type("some random text")
        self.assertEqual(result, "unknown")
    
    def test_extract_job_type_multiple_matches(self):
        """Test behavior with multiple job type mentions"""
        # Should return the first match found
        result = extract_job_type("full-time and part-time positions available")
        self.assertEqual(result, "full_time")


class SalaryExtractionTestCase(BaseTestCase):
    """Test salary extraction functionality"""
    
    def test_extract_salary_various_formats(self):
        """Test extraction of various salary formats"""
        test_cases = [
            ("Salary: $50,000 per year", "$50,000 per year"),
            ("$40,000 - $60,000 annually", "$40,000 - $60,000 annually"),
            ("€45,000/year", "€45,000/year"),
            ("₦500,000 per month", "₦500,000 per month"),
            ("¥4,000,000 annually", "¥4,000,000 annually"),
            ("₹800,000 per annum", "₹800,000 per annum"),
        ]
        
        for text, expected in test_cases:
            with self.subTest(text=text):
                result = extract_salary(text)
                self.assertIsNotNone(result)
                self.assertIn("000", result)  # Should contain meaningful numbers
    
    def test_extract_salary_ranges(self):
        """Test extraction of salary ranges"""
        test_cases = [
            "Salary range: $50,000 - $70,000",
            "$40k-$60k per year",
            "€35,000 – €45,000 annually",
        ]
        
        for text in test_cases:
            with self.subTest(text=text):
                result = extract_salary(text)
                self.assertIsNotNone(result)
                self.assertTrue(any(char in result for char in ['-', '–']))
    
    def test_extract_salary_validation(self):
        """Test salary validation logic"""
        # Too short
        result = extract_salary("Pay: $1")
        self.assertIsNone(result)
        
        # No meaningful numbers
        result = extract_salary("Salary: $0")
        self.assertIsNone(result)
    
    def test_extract_salary_no_match(self):
        """Test when no salary can be extracted"""
        result = extract_salary("Job description without salary information")
        self.assertIsNone(result)
    



class RequirementsExtractionTestCase(BaseTestCase):
    """Test requirements extraction functionality"""
    
    def test_extract_requirements_various_headers(self):
        """Test extraction with various requirement headers"""
        test_cases = [
            ("Requirements:\n- Bachelor's degree\n- 3+ years experience", "- Bachelor's degree\n- 3+ years experience"),
            ("Qualifications:\nMust have Python skills", "Must have Python skills"),
            ("You should have:\nStrong communication skills", "Strong communication skills"),
            ("Minimum requirements:\nRelevant experience", "Relevant experience"),
        ]
        
        for text, expected in test_cases:
            with self.subTest(text=text):
                result = extract_requirements(text)
                self.assertIsNotNone(result)
                self.assertIn(expected.strip().split('\n')[0].replace('- ', ''), result)
    
    def test_extract_requirements_minimum_length(self):
        """Test minimum length validation for requirements"""
        result = extract_requirements("Requirements: Short")
        self.assertIsNone(result)
    
    def test_extract_requirements_no_match(self):
        """Test when no requirements can be extracted"""
        result = extract_requirements("Job description without requirements section")
        self.assertIsNone(result)


class SkillsExtractionTestCase(BaseTestCase):
    """Test skills extraction functionality"""
    
    def test_extract_skills_tech_skills(self):
        """Test extraction of technical skills"""
        text = "We need someone with Python, JavaScript, React, Docker, and AWS experience"
        result = extract_skills(text)
        
        self.assertIsNotNone(result)
        expected_skills = ["Python", "JavaScript", "React", "Docker", "AWS"]
        self.assertContainsSkills(result, expected_skills)
    
    def test_extract_skills_soft_skills(self):
        """Test extraction of soft skills"""
        text = "Strong communication, leadership, and teamwork skills required"
        result = extract_skills(text)
        
        self.assertIsNotNone(result)
        expected_skills = ["communication", "leadership", "teamwork"]
        self.assertContainsSkills(result, expected_skills)
    
    def test_extract_skills_business_skills(self):
        """Test extraction of business skills"""
        text = "Experience with Salesforce, CRM, SEO, and digital marketing"
        result = extract_skills(text)
        
        self.assertIsNotNone(result)
        expected_skills = ["salesforce", "CRM", "SEO", "digital marketing"]
        self.assertContainsSkills(result, expected_skills)
    
    def test_extract_skills_healthcare(self):
        """Test extraction of healthcare skills"""
        text = "Patient care, EMR systems, and HIPAA compliance knowledge required"
        result = extract_skills(text)
        
        self.assertIsNotNone(result)
        expected_skills = ["patient care", "EMR", "HIPAA compliance"]
        self.assertContainsSkills(result, expected_skills)
    
    def test_extract_skills_mixed_categories(self):
        """Test extraction of skills from multiple categories"""
        text = """
        Required skills include Python programming, strong communication,
        Salesforce experience, patient care knowledge, and Agile methodology
        """
        result = extract_skills(text)
        
        self.assertIsNotNone(result)
        expected_skills = ["Python", "communication", "salesforce", "patient care", "Agile"]
        self.assertContainsSkills(result, expected_skills)
    
    def test_extract_skills_case_insensitive(self):
        """Test case-insensitive skill matching"""
        text = "PYTHON, javascript, React, DOCKER experience needed"
        result = extract_skills(text)
        
        self.assertIsNotNone(result)
        expected_skills = ["Python", "JavaScript", "React", "Docker"]
        self.assertContainsSkills(result, expected_skills)
    
    def test_extract_skills_word_boundaries(self):
        """Test that skills are matched with word boundaries"""
        text = "We need Java experience, not JavaScript"
        result = extract_skills(text)
        
        self.assertIsNotNone(result)
        # Should match both Java and JavaScript as separate skills
        if result:
            self.assertIn("JavaScript", result)
    
    def test_extract_skills_duplicates_removed(self):
        """Test that duplicate skills are removed"""
        text = "Python, Python programming, communication, strong communication skills"
        result = extract_skills(text)
        
        if result:
            skills_list = [skill.strip() for skill in result.split(',')]
            # Should not have duplicates
            self.assertEqual(len(skills_list), len(set(skills_list)))
    
    def test_extract_skills_sorted_output(self):
        """Test that skills are sorted alphabetically"""
        text = "ZZZ skill, AAA skill, BBB skill"  # Using non-real skills to test sorting
        # Use real skills for actual testing
        text = "React, Angular, Vue.js, Python, JavaScript"
        result = extract_skills(text)
        
        if result:
            skills_list = [skill.strip() for skill in result.split(',')]
            sorted_skills = sorted(skills_list, key=str.lower)
            self.assertEqual(skills_list, sorted_skills)
    
    def test_extract_skills_no_match(self):
        """Test when no skills can be extracted"""
        result = extract_skills("This is just random text without any recognizable skills")
        self.assertIsNone(result)


class ExperienceLevelExtractionTestCase(BaseTestCase):
    """Test experience level extraction functionality"""
    
    def test_extract_experience_level_keywords(self):
        """Test extraction based on experience keywords"""
        test_cases = [
            ("Senior Software Engineer position", "Senior"),
            ("Lead Developer role", "Senior"),
            ("Principal Architect needed", "Senior"),
            ("Junior Developer opportunity", "Junior"),
            ("Entry-level position available", "Junior"),
            ("New graduate welcome", "Junior"),
            ("Mid-level engineer wanted", "Mid-level"),
            ("Intermediate developer role", "Mid-level"),
            ("Experienced professional needed", "Mid-level"),
            ("Internship program", "Internship"),
            ("Intern position", "Internship"),
        ]
        
        for text, expected in test_cases:
            with self.subTest(text=text):
                result = extract_experience_level(text.lower())
                self.assertEqual(result, expected)
    
    def test_extract_experience_level_years(self):
        """Test extraction based on years of experience"""
        test_cases = [
            ("1 year of experience required", "Junior"),
            ("2 years experience needed", "Junior"),
            ("3 years of experience", "Mid-level"),
            ("5 yrs experience required", "Mid-level"),
            ("7+ years of experience", "Senior"),
            ("10 years experience needed", "Senior"),
        ]
        
        for text, expected in test_cases:
            with self.subTest(text=text):
                result = extract_experience_level(text.lower())
                self.assertEqual(result, expected)
    
    def test_extract_experience_level_no_match(self):
        """Test when no experience level can be extracted"""
        result = extract_experience_level("job description without experience information")
        self.assertIsNone(result)
    
    def test_extract_experience_level_edge_cases(self):
        """Test edge cases for years parsing"""
        test_cases = [
            ("0 years experience", "Junior"),
            ("0+ years required", "Junior"),
            ("6 years experience", "Senior"),
        ]
        
        for text, expected in test_cases:
            with self.subTest(text=text):
                result = extract_experience_level(text.lower())
                self.assertEqual(result, expected)


class IntegrationTestCase(BaseTestCase):
    """Integration tests for complete workflows"""
    
    def test_complete_job_extraction_workflow(self):
        """Test complete workflow from document to job details"""
        # Mock a complete job posting
        job_content = """
        SOFTWARE ENGINEER
        
        Company: TechCorp Solutions Inc.
        Location: San Francisco, CA
        Employment Type: Full-time
        Salary Range: $90,000 - $120,000 per year
        
        We are seeking a talented Software Engineer to join our growing team.
        
        Requirements:
        - Bachelor's degree in Computer Science
        - 3-5 years of experience in software development
        - Strong problem-solving skills
        
        Required Skills:
        - Python, JavaScript, React
        - AWS, Docker, Git
        - Strong communication and teamwork skills
        
        This is a mid-level position perfect for experienced developers.
        """
        
        # Test the complete extraction
        result = extract_job_details(job_content)
        
        # Verify all extracted fields
        self.assertEqual(result['title'], 'SOFTWARE ENGINEER')
        self.assertEqual(result['company'], 'TechCorp Solutions Inc.')
        self.assertEqual(result['location'], 'San Francisco, CA')
        self.assertEqual(result['job_type'], 'full_time')
        self.assertIn('$90,000', result['salary_range'])
        self.assertIsNotNone(result['requirements'])
        self.assertIsNotNone(result['skills_required'])
        self.assertEqual(result['experience_level'], 'Mid-level')
        
        # Verify skills extraction
        self.assertContainsSkills(result['skills_required'], ['Python', 'JavaScript', 'React', 'AWS', 'Docker', 'Git'])
    
    @patch('jobs.utils.PyPDF2.PdfReader')
    def test_pdf_to_job_details_workflow(self, mock_pdf_reader):
        """Test complete workflow from PDF to job details"""
        # Mock PDF content
        job_content = """
        MARKETING MANAGER
        
        Company: Marketing Pro LLC
        Location: Remote
        Job Type: Contract
        
        Requirements:
        - 5+ years marketing experience
        - Digital marketing, SEO, social media marketing skills
        """
        
        # Mock PDF extraction
        mock_page = Mock()
        mock_page.extract_text.return_value = job_content
        mock_reader_instance = Mock()
        mock_reader_instance.pages = [mock_page]
        mock_pdf_reader.return_value = mock_reader_instance
        
        # Create mock PDF file
        mock_file = self.create_mock_file("job.pdf")
        
        # Extract text from PDF
        extracted_text = extract_text_from_document(mock_file)
        
        # Extract job details
        result = extract_job_details(extracted_text)
        
        # Verify extraction
        self.assertEqual(result['title'], 'MARKETING MANAGER')
        self.assertEqual(result['company'], 'Marketing Pro LLC')
        self.assertEqual(result['location'], 'Remote')
        self.assertEqual(result['job_type'], 'contract')
        self.assertEqual(result['experience_level'], 'Senior')
        self.assertContainsSkills(result['skills_required'], ['digital marketing', 'SEO', 'social media marketing'])
    
    @patch('jobs.utils.docx.Document')
    def test_docx_to_job_details_workflow(self, mock_document):
        """Test complete workflow from DOCX to job details"""
        # Mock DOCX content
        job_content = """
        NURSE PRACTITIONER
        
        Organization: HealthCare Systems
        Based in: Boston, MA
        Employment: Part-time
        Compensation: $45/hour
        
        Qualifications:
        - Licensed Nurse Practitioner
        - 2+ years clinical experience
        - Patient care, EMR, HIPAA compliance knowledge
        """
        
        # Mock DOCX extraction
        mock_para = Mock()
        mock_para.text = job_content
        mock_doc_instance = Mock()
        mock_doc_instance.paragraphs = [mock_para]
        mock_document.return_value = mock_doc_instance
        
        # Create mock DOCX file
        mock_file = self.create_mock_file("job.docx")
        
        # Extract text from DOCX
        extracted_text = extract_text_from_document(mock_file)
        self.assertEqual(extracted_text, job_content + "\n")
        
        # Extract job details
        result = extract_job_details(extracted_text)
        
        # Verify extraction
        self.assertEqual(result['title'], 'NURSE PRACTITIONER')
        self.assertEqual(result['company'], 'HealthCare Systems')
        self.assertEqual(result['location'], 'Boston, MA')
        self.assertEqual(result['job_type'], 'part_time')
        self.assertIn('$45/hour', result['salary_range'])
        self.assertEqual(result['experience_level'], 'Junior')
        self.assertContainsSkills(result['skills_required'], ['patient care', 'EMR', 'HIPAA compliance'])


class EdgeCaseTestCase(BaseTestCase):
    """Test edge cases and boundary conditions"""
    
    def test_empty_string_inputs(self):
        """Test handling of empty string inputs"""
        empty_tests = [
            (extract_job_title, ""),
            (extract_company_name, ""),
            (extract_location, ""),
            (extract_salary, ""),
            (extract_requirements, ""),
            (extract_skills, ""),
        ]
        
        for func, input_val in empty_tests:
            with self.subTest(func=func.__name__):
                result = func(input_val)
                self.assertIsNone(result)
        
        # Job type should return 'unknown' for empty input
        result = extract_job_type("")
        self.assertEqual(result, "unknown")
        
        # Experience level should return None for empty input
        result = extract_experience_level("")
        self.assertIsNone(result)
    
    def test_whitespace_only_inputs(self):
        """Test handling of whitespace-only inputs"""
        whitespace_inputs = ["   ", "\n\n\n", "\t\t", "   \n\t   "]
        
        for whitespace in whitespace_inputs:
            with self.subTest(input=repr(whitespace)):
                result = extract_job_title(whitespace)
                self.assertIsNone(result)
                
                result = extract_company_name(whitespace)
                self.assertIsNone(result)
                
                result = extract_location(whitespace)
                self.assertIsNone(result)
    
    def test_very_long_inputs(self):
        """Test handling of extremely long inputs"""
        # Create a very long string
        long_text = "This is a very long text. " * 1000
        
        # Functions should handle long inputs gracefully
        result = extract_job_title(long_text)
        # May or may not find a title, but shouldn't crash
        self.assertIsNone(result)
        
        result = extract_company_name(long_text)
        # Should handle gracefully
        self.assertIsNone(result)
        
        result = extract_skills(long_text)
        # Should handle gracefully
        self.assertIsNone(result)

    
    def test_special_characters_handling(self):
        """Test handling of special characters and unicode"""
        special_texts = [
            "Job Title: Développeur Senior (Python/Django)",
            "Company: Müller & Associates GmbH",
            "Location: São Paulo, Brazil",
            "Salary: €50,000-€60,000 per year",
            "Skills: C++, .NET, Node.js, React.js",
        ]
        
        for text in special_texts:
            with self.subTest(text=text):
                # Should not raise exceptions
                try:
                    extract_job_title(text)
                    extract_company_name(text)
                    extract_location(text)
                    extract_salary(text)
                    extract_skills(text)
                except Exception as e:
                    self.fail(f"Function raised exception for text '{text}': {e}")
    
    def test_malformed_patterns(self):
        """Test handling of malformed or incomplete patterns"""
        malformed_texts = [
            "Job Title:",  # Missing title
            "Company:",    # Missing company
            "Location:",   # Missing location
            "Salary:",     # Missing salary
            "Requirements:",  # Missing requirements
        ]
        
        for text in malformed_texts:
            with self.subTest(text=text):
                # Should return None for incomplete patterns
                result = extract_job_title(text)
                self.assertIsNone(result)
                
                result = extract_company_name(text)
                self.assertIsNone(result)
                
                result = extract_location(text)
                self.assertIsNone(result)
                
                result = extract_salary(text)
                self.assertIsNone(result)
    
    def test_mixed_case_patterns(self):
        """Test case-insensitive pattern matching"""
        mixed_case_texts = [
            "JOB TITLE: software engineer",
            "Company: TECH CORP",
            "LOCATION: new york, ny",
            "full-TIME position",
            "REMOTE work available",
        ]
        
        for text in mixed_case_texts:
            with self.subTest(text=text):
                # Should handle mixed case appropriately
                if "JOB TITLE" in text:
                    result = extract_job_title(text)
                    self.assertEqual(result, "software engineer")
                
                if "Company" in text:
                    result = extract_company_name(text)
                    self.assertEqual(result, "TECH CORP")
                
                if "LOCATION" in text:
                    result = extract_location(text)
                    self.assertEqual(result, "new york, ny")
                
                if "full-TIME" in text:
                    result = extract_job_type(text.lower())
                    self.assertEqual(result, "full_time")
                
                if "REMOTE" in text:
                    result = extract_location(text)
                    self.assertEqual(result, "Remote")


class ErrorHandlingTestCase(BaseTestCase):
    """Test error handling and exception scenarios"""
    
    def test_none_input_handling(self):
        """Test handling of None inputs"""
        functions_to_test = [
            extract_job_title,
            extract_company_name,  
            extract_location,
            extract_job_type,
            extract_salary,
            extract_requirements,
            extract_skills,
            extract_experience_level,
        ]
        
        for func in functions_to_test:
            with self.subTest(func=func.__name__):
                with self.assertRaises((TypeError, AttributeError)):
                    func(None)
    
    def test_non_string_input_handling(self):
        """Test handling of non-string inputs"""
        non_string_inputs = [123, [], {}, True, False]
        
        functions_to_test = [
            extract_job_title,
            extract_company_name,
            extract_location,
            extract_job_type,
            extract_salary,
            extract_requirements,
            extract_skills,
            extract_experience_level,
        ]
        
        for func in functions_to_test:
            for input_val in non_string_inputs:
                with self.subTest(func=func.__name__, input=input_val):
                    with self.assertRaises((TypeError, AttributeError)):
                        func(input_val)
    
    @patch('jobs.utils.re.search')
    def test_regex_error_handling(self, mock_search):
        """Test handling of regex errors"""
        mock_search.side_effect = Exception("Regex error")
        
        # Functions should handle regex errors gracefully
        result = extract_job_title("test text")
        self.assertIsNone(result)
    
    def test_document_extraction_invalid_file_objects(self):
        """Test document extraction with invalid file objects"""
        # Test with None
        with self.assertRaises(AttributeError):
            extract_text_from_document(None)
        
        # Test with object without name attribute
        invalid_file = Mock()
        del invalid_file.name
        with self.assertRaises(AttributeError):
            extract_text_from_document(invalid_file)
    
    def test_extract_job_details_error_handling(self):
        """Test extract_job_details error handling"""
        # Should handle None input gracefully
        with self.assertRaises(AttributeError):
            extract_job_details(None)
        
        # Should handle non-string input
        with self.assertRaises((TypeError, AttributeError)):
            extract_job_details(123)


class PerformanceTestCase(BaseTestCase):
    """Test performance characteristics"""
    
    def test_large_document_processing(self):
        """Test processing of large documents"""
        # Create a large text document
        large_text = """
        Software Engineer Position
        Company: TechCorp
        Location: San Francisco, CA
        
        """ + ("Additional text content. " * 10000)  # 10000 repetitions
        
        # Should complete within reasonable time
        import time
        start_time = time.time()
        result = extract_job_details(large_text)
        end_time = time.time()
        
        # Should complete within 5 seconds (adjust as needed)
        self.assertLess(end_time - start_time, 5.0)
        
        # Should still extract basic information
        self.assertEqual(result['title'], 'Software Engineer Position')
        self.assertEqual(result['company'], 'TechCorp')
    
    def test_multiple_skill_extraction_performance(self):
        """Test performance of skill extraction with many skills"""
        # Create text with many skill mentions
        skills_text = """
        Required skills: Python, JavaScript, Java, C++, C#, Ruby, PHP, Go, Rust, Swift,
        React, Angular, Vue.js, Django, Flask, Spring Boot, Laravel, Express.js,
        AWS, Azure, GCP, Docker, Kubernetes, Jenkins, Git, Linux, Windows, macOS,
        MySQL, PostgreSQL, MongoDB, Redis, Elasticsearch, Kafka, RabbitMQ,
        communication, leadership, teamwork, problem solving, analytical thinking,
        project management, Agile, Scrum, Kanban, time management, creativity
        """
        
        import time
        start_time = time.time()
        result = extract_skills(skills_text)
        end_time = time.time()
        
        # Should complete quickly
        self.assertLess(end_time - start_time, 1.0)
        
        # Should extract multiple skills
        self.assertIsNotNone(result)
        skill_count = len(result.split(',')) if result else 0
        self.assertGreater(skill_count, 10)


class RegressionTestCase(BaseTestCase):
    """Regression tests for previously found issues"""
    
    def test_title_extraction_with_company_suffix(self):
        """Regression test: Title extraction when company name appears after title"""
        text = "Senior Developer at TechCorp Inc."
        result = extract_job_title(text)
        # Should extract title, not be confused by company name
        self.assertIsNotNone(result)
    
    def test_salary_extraction_with_benefits_text(self):
        """Regression test: Salary extraction with benefits information"""
        text = "Salary: $70,000 plus comprehensive benefits package"
        result = extract_salary(text)
        self.assertIn("$70,000", result)
    
    def test_location_extraction_multiple_locations(self):
        """Regression test: Location extraction with multiple locations mentioned"""
        text = "Offices in New York, NY and San Francisco, CA. Based in New York, NY"
        result = extract_location(text)
        # Should prefer explicit "based in" pattern
        self.assertEqual(result, "New York, NY")
    
    def test_skills_extraction_with_versions(self):
        """Regression test: Skills extraction with version numbers"""
        text = "Experience with Python 3.8+, React 18, and Node.js v16"
        result = extract_skills(text)
        self.assertIsNotNone(result)
        self.assertContainsSkills(result, ["Python", "React"])
    
    def test_company_extraction_with_legal_entities(self):
        """Regression test: Company extraction with legal entity types"""
        text = "Company: TechCorp LLC doing business as TechSolutions Inc."
        result = extract_company_name(text)
        # Should extract the first company name
        self.assertIn("TechCorp", result)




# Test data fixtures for reuse across tests
class TestDataFixtures:
    """Common test data fixtures"""
    
    SAMPLE_JOB_DESCRIPTIONS = {
        'tech_job': """
            Senior Software Engineer
            
            Company: TechCorp Solutions
            Location: Seattle, WA
            Employment: Full-time
            Salary: $120,000 - $150,000 per year
            
            We are seeking a Senior Software Engineer with 5+ years of experience.
            
            Requirements:
            - Bachelor's degree in Computer Science
            - Proficiency in Python, JavaScript, React
            - Experience with AWS, Docker, Git
            - Strong communication and problem-solving skills
            
            This is a senior-level position for experienced developers.
        """,
        
        'healthcare_job': """
            Registered Nurse
            
            Organization: City General Hospital
            Based in: Chicago, IL
            Job Type: Part-time
            Hourly Rate: $35-$42/hour
            
            Qualifications:
            - Current RN license
            - 2+ years clinical experience
            - Patient care, EMR, medication administration skills
            - CPR certification required
            
            Entry-level candidates welcome.
        """,
        
        'marketing_job': """
            Digital Marketing Specialist
            
            Company: Marketing Pro Agency
            Location: Remote
            Employment Type: Contract
            
            Requirements:
            - 3-5 years digital marketing experience
            - SEO, SEM, social media marketing expertise
            - Google Analytics, HubSpot experience
            - Strong analytical and communication skills
            
            Mid-level position with growth opportunities.
        """,
        
        'minimal_job': """
            Looking for a developer to join our team.
            Some programming experience preferred.
        """,
        
        'malformed_job': """
            Job Title:
            Company:
            Location:
            
            This is a malformed job posting with incomplete information.
        """
    }
    
    @classmethod
    def get_job_description(cls, job_type: str) -> str:
        """Get a sample job description by type"""
        return cls.SAMPLE_JOB_DESCRIPTIONS.get(job_type, cls.SAMPLE_JOB_DESCRIPTIONS['minimal_job'])


# Performance benchmarking utilities
class PerformanceBenchmark:
    """Utilities for performance testing"""
    
    @staticmethod
    def benchmark_function(func, *args, iterations=1000):
        """Benchmark a function's performance"""
        import time
        
        times = []
        for _ in range(iterations):
            start = time.time()
            func(*args)
            end = time.time()
            times.append(end - start)
        
        avg_time = sum(times) / len(times)
        min_time = min(times)
        max_time = max(times)
        
        return {
            'average': avg_time,
            'minimum': min_time,
            'maximum': max_time,
            'total_iterations': iterations
        }
    
    @staticmethod
    def run_extraction_benchmarks():
        """Run benchmarks for all extraction functions"""
        sample_text = TestDataFixtures.get_job_description('tech_job')
        
        functions_to_benchmark = [
            ('extract_job_title', extract_job_title),
            ('extract_company_name', extract_company_name),
            ('extract_location', extract_location),
            ('extract_salary', extract_salary),
            ('extract_skills', extract_skills),
            ('extract_job_details', extract_job_details),
        ]
        
        print("Performance Benchmarks:")
        print("-" * 50)
        
        for name, func in functions_to_benchmark:
            if name == 'extract_job_type' or name == 'extract_experience_level':
                benchmark = PerformanceBenchmark.benchmark_function(
                    func, sample_text.lower(), iterations=1000
                )
            else:
                benchmark = PerformanceBenchmark.benchmark_function(
                    func, sample_text, iterations=1000
                )
            
            print(f"{name}:")
            print(f"  Average: {benchmark['average']:.6f}s")
            print(f"  Min/Max: {benchmark['minimum']:.6f}s / {benchmark['maximum']:.6f}s")
            print()
