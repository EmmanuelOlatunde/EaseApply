import logging
from django.core.files.uploadedfile import UploadedFile

try:
    import PyPDF2
except ImportError:
    PyPDF2 = None

try:
    from docx import Document
except ImportError:
    Document = None

logger = logging.getLogger(__name__)

class TextExtractionError(Exception):
    """Custom exception for text extraction errors"""
    pass

def extract_text_from_pdf(file) -> str:
    """
    Extract text from PDF file using PyPDF2
    
    Args:
        file: Django UploadedFile or file-like object
        
    Returns:
        str: Extracted text content
        
    Raises:
        TextExtractionError: If extraction fails
    """
    if PyPDF2 is None:
        raise TextExtractionError("PyPDF2 is not installed. Install with: pip install PyPDF2")
    
    try:
        # Reset file pointer to beginning
        file.seek(0)
        
        pdf_reader = PyPDF2.PdfReader(file)
        text_content = []
        
        for page_num, page in enumerate(pdf_reader.pages):
            try:
                page_text = page.extract_text()
                if page_text.strip():
                    text_content.append(page_text)
            except Exception as e:
                logger.warning(f"Failed to extract text from page {page_num + 1}: {str(e)}")
                continue
        
        if not text_content:
            raise TextExtractionError("No text could be extracted from the PDF")
            
        return '\n\n'.join(text_content)
        
    except Exception as e:
        logger.error(f"PDF text extraction failed: {str(e)}")
        raise TextExtractionError(f"Failed to extract text from PDF: {str(e)}")
    finally:
        # Reset file pointer
        file.seek(0)

def extract_text_from_docx(file) -> str:
    """
    Extract text from DOCX file using python-docx
    
    Args:
        file: Django UploadedFile or file-like object
        
    Returns:
        str: Extracted text content
        
    Raises:
        TextExtractionError: If extraction fails
    """
    if Document is None:
        raise TextExtractionError("python-docx is not installed. Install with: pip install python-docx")
    
    try:
        # Reset file pointer to beginning
        file.seek(0)
        
        doc = Document(file)
        text_content = []
        
        # Extract text from paragraphs
        for paragraph in doc.paragraphs:
            if paragraph.text.strip():
                text_content.append(paragraph.text)
        
        # Extract text from tables
        for table in doc.tables:
            for row in table.rows:
                row_text = []
                for cell in row.cells:
                    if cell.text.strip():
                        row_text.append(cell.text.strip())
                if row_text:
                    text_content.append(' | '.join(row_text))
        
        if not text_content:
            raise TextExtractionError("No text could be extracted from the DOCX file")
            
        return '\n\n'.join(text_content)
        
    except Exception as e:
        logger.error(f"DOCX text extraction failed: {str(e)}")
        raise TextExtractionError(f"Failed to extract text from DOCX: {str(e)}")
    finally:
        # Reset file pointer
        file.seek(0)

def extract_text_from_resume(file, file_type: str) -> str:
    """
    Extract text from resume file based on file type
    
    Args:
        file: Django UploadedFile or file-like object
        file_type: Either 'pdf' or 'docx'
        
    Returns:
        str: Extracted text content
        
    Raises:
        TextExtractionError: If extraction fails or unsupported file type
    """
    file_type = file_type.lower()
    
    if file_type == 'pdf':
        return extract_text_from_pdf(file)
    elif file_type in ['docx', 'doc']:
        return extract_text_from_docx(file)
    else:
        raise TextExtractionError(f"Unsupported file type: {file_type}")

def validate_resume_file(file: UploadedFile) -> tuple[str, bool]:
    """
    Validate uploaded resume file
    
    Args:
        file: Django UploadedFile
        
    Returns:
        tuple: (file_type, is_valid)
    """
    if not file:
        return '', False
    
    # Check file size (limit to 10MB)
    max_size = 10 * 1024 * 1024  # 10MB
    if file.size > max_size:
        return '', False
    
    # Get file extension
    filename = file.name.lower()
    if filename.endswith('.pdf'):
        return 'pdf', True
    elif filename.endswith(('.docx', '.doc')):
        return 'docx', True


    return '', False