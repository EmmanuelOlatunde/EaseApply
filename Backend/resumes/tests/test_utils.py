from unittest.mock import patch, MagicMock
from django.test import TestCase
from django.core.files.uploadedfile import SimpleUploadedFile
from ..utils import (
    extract_text_from_pdf,
    extract_text_from_docx,
    extract_text_from_resume,
    validate_resume_file,
    TextExtractionError
)

class TextExtractionUtilsTestCase(TestCase):
    """Test cases for text extraction utilities"""
    
    def setUp(self):
        """Set up test data"""
        self.pdf_content = b'%PDF-1.4 fake pdf content'
        self.docx_content = b'fake docx content'
        self.large_content = b'x' * (11 * 1024 * 1024)  # 11MB

class PDFTextExtractionTestCase(TextExtractionUtilsTestCase):
    """Test cases for PDF text extraction"""
    
    @patch('resumes.utils.PyPDF2')
    def test_extract_text_from_pdf_success(self, mock_pypdf2):
        """Test successful PDF text extraction"""
        # Mock PdfReader and pages
        mock_page1 = MagicMock()
        mock_page1.extract_text.return_value = "Page 1 content"
        mock_page2 = MagicMock()
        mock_page2.extract_text.return_value = "Page 2 content"
        
        mock_reader = MagicMock()
        mock_reader.pages = [mock_page1, mock_page2]
        
        mock_pypdf2.PdfReader.return_value = mock_reader
        
        # Create test file
        pdf_file = SimpleUploadedFile(
            "test.pdf", self.pdf_content, content_type="application/pdf"
        )
        
        result = extract_text_from_pdf(pdf_file)
        
        expected_text = "Page 1 content\n\nPage 2 content"
        self.assertEqual(result, expected_text)
        mock_pypdf2.PdfReader.assert_called_once()
    
    @patch('resumes.utils.PyPDF2')
    def test_extract_text_from_pdf_empty_pages(self, mock_pypdf2):
        """Test PDF with empty pages"""
        mock_page1 = MagicMock()
        mock_page1.extract_text.return_value = ""  # Empty page
        mock_page2 = MagicMock()
        mock_page2.extract_text.return_value = "   "  # Whitespace only
        mock_page3 = MagicMock()
        mock_page3.extract_text.return_value = "Actual content"
        
        mock_reader = MagicMock()
        mock_reader.pages = [mock_page1, mock_page2, mock_page3]
        
        mock_pypdf2.PdfReader.return_value = mock_reader
        
        pdf_file = SimpleUploadedFile("test.pdf", self.pdf_content)
        result = extract_text_from_pdf(pdf_file)
        
        self.assertEqual(result, "Actual content")
    
    @patch('resumes.utils.PyPDF2')
    def test_extract_text_from_pdf_no_text(self, mock_pypdf2):
        """Test PDF with no extractable text"""
        mock_page = MagicMock()
        mock_page.extract_text.return_value = ""
        
        mock_reader = MagicMock()
        mock_reader.pages = [mock_page]
        
        mock_pypdf2.PdfReader.return_value = mock_reader
        
        pdf_file = SimpleUploadedFile("test.pdf", self.pdf_content)
        
        with self.assertRaises(TextExtractionError) as context:
            extract_text_from_pdf(pdf_file)
        
        self.assertIn("No text could be extracted", str(context.exception))
    
    @patch('resumes.utils.PyPDF2')
    def test_extract_text_from_pdf_pypdf2_error(self, mock_pypdf2):
        """Test PDF extraction with PyPDF2 error"""
        mock_pypdf2.PdfReader.side_effect = Exception("PyPDF2 error")
        
        pdf_file = SimpleUploadedFile("test.pdf", self.pdf_content)
        
        with self.assertRaises(TextExtractionError) as context:
            extract_text_from_pdf(pdf_file)
        
        self.assertIn("Failed to extract text from PDF", str(context.exception))
    
    @patch('resumes.utils.PyPDF2', None)
    def test_extract_text_from_pdf_pypdf2_not_installed(self):
        """Test PDF extraction when PyPDF2 is not installed"""
        pdf_file = SimpleUploadedFile("test.pdf", self.pdf_content)
        
        with self.assertRaises(TextExtractionError) as context:
            extract_text_from_pdf(pdf_file)
        
        self.assertIn("PyPDF2 is not installed", str(context.exception))
    
    @patch('resumes.utils.PyPDF2')
    def test_extract_text_from_pdf_page_error(self, mock_pypdf2):
        """Test PDF extraction with individual page errors"""
        mock_page1 = MagicMock()
        mock_page1.extract_text.side_effect = Exception("Page error")
        mock_page2 = MagicMock()
        mock_page2.extract_text.return_value = "Page 2 content"
        
        mock_reader = MagicMock()
        mock_reader.pages = [mock_page1, mock_page2]
        
        mock_pypdf2.PdfReader.return_value = mock_reader
        
        pdf_file = SimpleUploadedFile("test.pdf", self.pdf_content)
        result = extract_text_from_pdf(pdf_file)
        
        # Should continue with other pages despite error
        self.assertEqual(result, "Page 2 content")
    
    def test_extract_text_from_pdf_file_pointer_reset(self):
        """Test that file pointer is reset after extraction"""
        pdf_file = SimpleUploadedFile("test.pdf", self.pdf_content)
        
        # Move file pointer
        pdf_file.seek(10)
        initial_position = pdf_file.tell()
        self.assertEqual(initial_position, 10)
        
        # Mock PyPDF2 to avoid actual extraction
        with patch('resumes.utils.PyPDF2') as mock_pypdf2:
            mock_reader = MagicMock()
            mock_reader.pages = []
            mock_pypdf2.PdfReader.return_value = mock_reader
            
            try:
                extract_text_from_pdf(pdf_file)
            except TextExtractionError:
                pass  # Expected due to no pages
            
            # File pointer should be reset to beginning
            self.assertEqual(pdf_file.tell(), 0)

class DOCXTextExtractionTestCase(TextExtractionUtilsTestCase):
    """Test cases for DOCX text extraction"""
    
    @patch('resumes.utils.Document')
    def test_extract_text_from_docx_success(self, mock_document_class):
        """Test successful DOCX text extraction"""
        # Mock paragraphs
        mock_para1 = MagicMock()
        mock_para1.text = "First paragraph"
        mock_para2 = MagicMock()
        mock_para2.text = "Second paragraph"
        
        # Mock document
        mock_doc = MagicMock()
        mock_doc.paragraphs = [mock_para1, mock_para2]
        mock_doc.tables = []  # No tables
        
        mock_document_class.return_value = mock_doc
        
        docx_file = SimpleUploadedFile("test.docx", self.docx_content)
        result = extract_text_from_docx(docx_file)
        
        expected_text = "First paragraph\n\nSecond paragraph"
        self.assertEqual(result, expected_text)
    
    @patch('resumes.utils.Document')
    def test_extract_text_from_docx_with_tables(self, mock_document_class):
        """Test DOCX extraction with tables"""
        # Mock paragraphs
        mock_para = MagicMock()
        mock_para.text = "Document paragraph"
        
        # Mock table cells
        mock_cell1 = MagicMock()
        mock_cell1.text = "Cell 1"
        mock_cell2 = MagicMock()
        mock_cell2.text = "Cell 2"
        mock_cell3 = MagicMock()
        mock_cell3.text = "Cell 3"
        mock_cell4 = MagicMock()
        mock_cell4.text = ""  # Empty cell
        
        # Mock table rows
        mock_row1 = MagicMock()
        mock_row1.cells = [mock_cell1, mock_cell2]
        mock_row2 = MagicMock()
        mock_row2.cells = [mock_cell3, mock_cell4]
        
        # Mock table
        mock_table = MagicMock()
        mock_table.rows = [mock_row1, mock_row2]
        
        # Mock document
        mock_doc = MagicMock()
        mock_doc.paragraphs = [mock_para]
        mock_doc.tables = [mock_table]
        
        mock_document_class.return_value = mock_doc
        
        docx_file = SimpleUploadedFile("test.docx", self.docx_content)
        result = extract_text_from_docx(docx_file)
        
        expected_text = "Document paragraph\n\nCell 1 | Cell 2\n\nCell 3"
        self.assertEqual(result, expected_text)
    
    @patch('resumes.utils.Document')
    def test_extract_text_from_docx_empty_content(self, mock_document_class):
        """Test DOCX with no extractable content"""
        mock_para = MagicMock()
        mock_para.text = ""  # Empty paragraph
        
        mock_doc = MagicMock()
        mock_doc.paragraphs = [mock_para]
        mock_doc.tables = []
        
        mock_document_class.return_value = mock_doc
        
        docx_file = SimpleUploadedFile("test.docx", self.docx_content)
        
        with self.assertRaises(TextExtractionError) as context:
            extract_text_from_docx(docx_file)
        
        self.assertIn("No text could be extracted", str(context.exception))
    
    @patch('resumes.utils.Document')
    def test_extract_text_from_docx_python_docx_error(self, mock_document_class):
        """Test DOCX extraction with python-docx error"""
        mock_document_class.side_effect = Exception("python-docx error")
        
        docx_file = SimpleUploadedFile("test.docx", self.docx_content)
        
        with self.assertRaises(TextExtractionError) as context:
            extract_text_from_docx(docx_file)
        
        self.assertIn("Failed to extract text from DOCX", str(context.exception))
    
    @patch('resumes.utils.Document', None)
    def test_extract_text_from_docx_not_installed(self):
        """Test DOCX extraction when python-docx is not installed"""
        docx_file = SimpleUploadedFile("test.docx", self.docx_content)
        
        with self.assertRaises(TextExtractionError) as context:
            extract_text_from_docx(docx_file)
        
        self.assertIn("python-docx is not installed", str(context.exception))
    
    @patch('resumes.utils.Document')
    def test_extract_text_from_docx_whitespace_handling(self, mock_document_class):
        """Test DOCX extraction with whitespace handling"""
        mock_para1 = MagicMock()
        mock_para1.text = "  Text with spaces  "
        mock_para2 = MagicMock()
        mock_para2.text = ""  # Empty
        mock_para3 = MagicMock()
        mock_para3.text = "   "  # Only whitespace
        mock_para4 = MagicMock()
        mock_para4.text = "Normal text"
        
        mock_doc = MagicMock()
        mock_doc.paragraphs = [mock_para1, mock_para2, mock_para3, mock_para4]
        mock_doc.tables = []
        
        mock_document_class.return_value = mock_doc
        
        docx_file = SimpleUploadedFile("test.docx", self.docx_content)
        result = extract_text_from_docx(docx_file)
        
        # Should only include non-empty paragraphs
        expected_text = "  Text with spaces  \n\nNormal text"
        self.assertEqual(result, expected_text)

class GeneralTextExtractionTestCase(TextExtractionUtilsTestCase):
    """Test cases for general text extraction function"""
    
    @patch('resumes.utils.extract_text_from_pdf')
    def test_extract_text_from_resume_pdf(self, mock_pdf_extract):
        """Test extract_text_from_resume with PDF"""
        mock_pdf_extract.return_value = "PDF extracted text"
        
        pdf_file = SimpleUploadedFile("test.pdf", self.pdf_content)
        result = extract_text_from_resume(pdf_file, 'pdf')
        
        self.assertEqual(result, "PDF extracted text")
        mock_pdf_extract.assert_called_once_with(pdf_file)
    
    @patch('resumes.utils.extract_text_from_docx')
    def test_extract_text_from_resume_docx(self, mock_docx_extract):
        """Test extract_text_from_resume with DOCX"""
        mock_docx_extract.return_value = "DOCX extracted text"
        
        docx_file = SimpleUploadedFile("test.docx", self.docx_content)
        result = extract_text_from_resume(docx_file, 'docx')
        
        self.assertEqual(result, "DOCX extracted text")
        mock_docx_extract.assert_called_once_with(docx_file)
    
    @patch('resumes.utils.extract_text_from_docx')
    def test_extract_text_from_resume_doc(self, mock_docx_extract):
        """Test extract_text_from_resume with DOC extension"""
        mock_docx_extract.return_value = "DOC extracted text"
        
        doc_file = SimpleUploadedFile("test.doc", self.docx_content)
        result = extract_text_from_resume(doc_file, 'doc')
        
        self.assertEqual(result, "DOC extracted text")
        mock_docx_extract.assert_called_once_with(doc_file)
    
    def test_extract_text_from_resume_unsupported_type(self):
        """Test extract_text_from_resume with unsupported file type"""
        txt_file = SimpleUploadedFile("test.txt", b"text content")
        
        with self.assertRaises(TextExtractionError) as context:
            extract_text_from_resume(txt_file, 'txt')
        
        self.assertIn("Unsupported file type: txt", str(context.exception))
    
    def test_extract_text_from_resume_case_insensitive(self):
        """Test that file type matching is case insensitive"""
        with patch('resumes.utils.extract_text_from_pdf') as mock_pdf:
            mock_pdf.return_value = "PDF text"
            
            pdf_file = SimpleUploadedFile("test.pdf", self.pdf_content)
            
            # Test uppercase
            result = extract_text_from_resume(pdf_file, 'PDF')
            self.assertEqual(result, "PDF text")
            
            # Test mixed case
            result = extract_text_from_resume(pdf_file, 'Pdf')
            self.assertEqual(result, "PDF text")

class FileValidationTestCase(TextExtractionUtilsTestCase):
    """Test cases for file validation utilities"""
    
    def test_validate_resume_file_valid_pdf(self):
        """Test validation of valid PDF file"""
        pdf_file = SimpleUploadedFile(
            "resume.pdf", self.pdf_content, content_type="application/pdf"
        )
        
        file_type, is_valid = validate_resume_file(pdf_file)
        
        self.assertEqual(file_type, 'pdf')
        self.assertTrue(is_valid)
    
    def test_validate_resume_file_valid_docx(self):
        """Test validation of valid DOCX file"""
        docx_file = SimpleUploadedFile(
            "resume.docx", self.docx_content,
            content_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )
        
        file_type, is_valid = validate_resume_file(docx_file)
        
        self.assertEqual(file_type, 'docx')
        self.assertTrue(is_valid)
    
    # def test_validate_resume_file_valid_doc(self):
    #     """Test validation of valid DOC file"""
    #     doc_file = SimpleUploadedFile(
    #         "resume.doc", self.docx_content,
    #         content_type="application/msword"
    #     )
        
    #     file_type, is_valid = validate_resume_file(doc_file)
        
    #     self.assertEqual(file_type, '

class IncompleteFileValidationTestCase(TestCase):
    """Complete the incomplete test from test_utils.py"""
    
    def test_validate_resume_file_valid_doc(self):
        """Test validation of valid DOC file - completing the incomplete test"""
        doc_file = SimpleUploadedFile(
            "resume.doc", 
            b'fake doc content',
            content_type="application/msword"
        )
        
        file_type, is_valid = validate_resume_file(doc_file)
        
        self.assertEqual(file_type, 'docx')  # DOC files are treated as DOCX
        self.assertTrue(is_valid)
    
    def test_validate_resume_file_unsupported_extensions(self):
        """Test validation with various unsupported file extensions"""
        unsupported_files = [
            ("resume.txt", "text/plain"),
            ("resume.jpg", "image/jpeg"),
            ("resume.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"),
            ("resume.ppt", "application/vnd.ms-powerpoint"),
            ("resume.zip", "application/zip"),
        ]
        
        for filename, content_type in unsupported_files:
            with self.subTest(filename=filename):
                unsupported_file = SimpleUploadedFile(
                    filename,
                    b'fake content',
                    content_type=content_type
                )
                
                file_type, is_valid = validate_resume_file(unsupported_file)
                self.assertEqual(file_type, '')
                self.assertFalse(is_valid)
