import logging
import re
from typing import Dict, List, Optional, Any
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

class ResumeParsingError(Exception):
    """Custom exception for resume parsing errors"""
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

def extract_full_name(text: str) -> Optional[str]:
    lines = text.strip().split('\n')
    for line in lines[:10]:
        if line.strip().lower().startswith('summary'):
            continue
        words = line.strip().split()
        if 2 <= len(words) <= 4 and all(w.isalpha() for w in words):
            return line.strip()
    return None


def extract_contact_info(text: str) -> Dict[str, Optional[str]]:
    """
    Extract contact information from resume text
    """
    contact_info = {
        'email': None,
        'phone': None,
        'address': None,
        'linkedin': None,
        'github': None
    }
    
    # Email extraction
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    email_match = re.search(email_pattern, text)
    if email_match:
        contact_info['email'] = email_match.group()
    
    # Phone extraction
    phone_patterns = [
        r'\b\d{3}[-.\s]?\d{3}[-.\s]?\d{4}\b',
        r'\(\d{3}\)\s?\d{3}[-.\s]?\d{4}',
        r'\+\d{1,3}[-.\s]?\d{3}[-.\s]?\d{3}[-.\s]?\d{4}'
    ]
    for pattern in phone_patterns:
        phone_match = re.search(pattern, text)
        if phone_match:
            contact_info['phone'] = phone_match.group()
            break
    
    # LinkedIn extraction
    linkedin_pattern = r'(https?://)?(www\.)?linkedin\.com/in/[A-Za-z0-9\-]+'
    linkedin_match = re.search(linkedin_pattern, text, re.IGNORECASE)
    if linkedin_match:
        contact_info['linkedin'] = linkedin_match.group()
    
    # GitHub extraction
    github_pattern = r'(https?://)?(www\.)?github\.com/[A-Za-z0-9\-]+'
    github_match = re.search(github_pattern, text, re.IGNORECASE)
    if github_match:
        contact_info['github'] = github_match.group()
    
    # Address extraction (basic)
    lines = text.split('\n')
    for line in lines[:10]:  # Check first 10 lines
        if re.search(r'\b\d{5}(-\d{4})?\b', line):  # ZIP code pattern
            contact_info['address'] = line.strip()
            break
    
    return contact_info

def extract_summary(text: str) -> Optional[str]:
    """
    Extract professional summary/objective from resume
    """
    summary_keywords = [
        'summary', 'professional summary', 'executive summary',
        'profile', 'professional profile', 'career summary',
        'objective', 'career objective', 'professional objective'
    ]
    
    lines = text.split('\n')
    summary_started = False
    summary_lines = []
    
    for i, line in enumerate(lines):
        line_lower = line.lower().strip()
        
        # Check if this line contains summary keywords
        if any(keyword in line_lower for keyword in summary_keywords):
            summary_started = True
            # If the keyword line has content after it, include it
            if len(line.strip()) > len(max(summary_keywords, key=len)):
                summary_lines.append(line.strip())
            continue
        
        if summary_started:
            # Stop if we hit another section header
            if (line.strip() and 
                any(section in line_lower for section in [
                    'experience', 'education', 'skills', 'employment',
                    'work history', 'projects', 'certifications'
                ])):
                break
            
            # Add non-empty lines to summary
            if line.strip():
                summary_lines.append(line.strip())
            elif summary_lines:  # Empty line after we've started collecting
                break
    
    return ' '.join(summary_lines) if summary_lines else None

def extract_skills(text: str) -> List[str]:
    """
    Extract skills from resume text
    """
    skills = []
    skills_keywords = ['skills', 'technical skills', 'core competencies', 'technologies']
    
    lines = text.split('\n')
    skills_section = False
    
    for line in lines:
        line_lower = line.lower().strip()
        
        if ':' in line:
            parts = line.split(':', 1)[1]
            skills += [s.strip() for s in re.split(r'[,\|]', parts)]

        # Check if we've entered skills section
        if any(keyword in line_lower for keyword in skills_keywords):
            skills_section = True
            continue
        
        if skills_section:
            # Stop if we hit another major section
            if any(section in line_lower for section in [
                'experience', 'education', 'employment', 'work history',
                'projects', 'certifications', 'summary', 'objective'
            ]):
                break
            
            if line.strip():
                # Split by common delimiters
                line_skills = re.split(r'[,•·|]', line)
                for skill in line_skills:
                    skill = skill.strip()
                    if skill and len(skill) > 1:
                        skills.append(skill)
    
    return skills

def extract_work_experience(text: str) -> List[Dict[str, Any]]:
    """
    Extract work experience entries from resume
    """
    experience = []
    exp_keywords = ['experience', 'work experience', 'employment', 'work history', 'career history']
    
    lines = text.split('\n')
    exp_section = False
    current_job = {}
    
    for line in lines:
        line_lower = line.lower().strip()
        
        # Check if we've entered experience section
        if any(keyword in line_lower for keyword in exp_keywords):
            exp_section = True
            continue
        
        if exp_section:
            # Stop if we hit another major section
            if any(section in line_lower for section in [
                'education', 'skills', 'projects', 'certifications'
            ]):
                if current_job:
                    experience.append(current_job)
                break
            
            if line.strip():
                # Check if this looks like a job title/company line
                if re.search(r'\d{4}', line):  # Contains year
                    if current_job:
                        experience. append(current_job)
                    current_job = {
                        'title': '',
                        'company': '',
                        'duration': '',
                        'description': []
                    }
                    
                    # Try to parse job title, company, and dates
                    parts = line.split('|')
                    if len(parts) >= 2:
                        current_job['title'] = parts[0].strip()
                        current_job['company'] = parts[1].strip()
                        if len(parts) >= 3:
                            current_job['duration'] = parts[2].strip()
                    else:
                        current_job['title'] = line.strip()
                
                elif current_job and (line.startswith('•') or line.startswith('-')):
                    # This is a bullet point description
                    current_job['description'].append(line.strip())
    
        if '|' in line:
            title_company, year = line.rsplit('|', 1)
            title, company = title_company.split(',', 1)

    if current_job:
        experience.append(current_job)
    
    return experience

def extract_education(text: str) -> List[Dict[str, str]]:
    """
    Extract education information from resume
    """
    education = []
    edu_keywords = ['education', 'academic background', 'qualifications']
    
    lines = text.split('\n')
    edu_section = False
    
    for line in lines:
        line_lower = line.lower().strip()
        
        # Check if we've entered education section
        if any(keyword in line_lower for keyword in edu_keywords):
            edu_section = True
            continue
        
        if edu_section:
            # Stop if we hit another major section
            if any(section in line_lower for section in [
                'experience', 'skills', 'projects', 'certifications'
            ]):
                break
            
            if line.strip() and re.search(r'\d{4}', line):  # Contains year
                education.append({
                    'degree': line.strip(),
                    'institution': '',
                    'year': re.search(r'\d{4}', line).group() if re.search(r'\d{4}', line) else ''
                })
    
    return education

def extract_certifications(text: str) -> List[str]:
    """
    Extract certifications from resume
    """
    certifications = []
    cert_keywords = ['certifications', 'certificates', 'professional certifications']
    
    lines = text.split('\n')
    cert_section = False
    
    for line in lines:
        line_lower = line.lower().strip()
        
        # Check if we've entered certifications section
        if any(keyword in line_lower for keyword in cert_keywords):
            cert_section = True
            continue
        
        if cert_section:
            # Stop if we hit another major section
            if any(section in line_lower for section in [
                'experience', 'education', 'skills', 'projects'
            ]):
                break
            
            if line.strip():
                certifications.append(line.strip())
    
    return certifications

def extract_projects(text: str) -> List[Dict[str, str]]:
    """
    Extract projects from resume
    """
    projects = []
    project_keywords = ['projects', 'personal projects', 'key projects']
    
    lines = text.split('\n')
    project_section = False
    current_project = {}
    
    for line in lines:
        line_lower = line.lower().strip()
        
        # Check if we've entered projects section
        if any(keyword in line_lower for keyword in project_keywords):
            project_section = True
            continue
        
        if project_section:
            # Stop if we hit another major section
            if any(section in line_lower for section in [
                'experience', 'education', 'skills', 'certifications'
            ]):
                if current_project:
                    projects.append(current_project)
                break
            
            if line.strip():
                if line.startswith('•') or line.startswith('-'):
                    if current_project:
                        if 'description' not in current_project:
                            current_project['description'] = []
                        current_project['description'].append(line.strip())
                else:
                    if current_project:
                        projects.append(current_project)
                    current_project = {
                        'name': line.strip(),
                        'description': []
                    }
    
    if current_project:
        projects.append(current_project)
    
    return projects

def parse_resume_content(extracted_text: str) -> Dict[str, Any]:
    """
    Parse extracted resume text into structured data
    
    Args:
        extracted_text: Raw text extracted from resume file
        
    Returns:
        Dict containing parsed resume information
        
    Raises:
        ResumeParsingError: If parsing fails
    """
    try:
        parsed_data = {
            'fullName': extract_full_name(extracted_text),
            'summary': extract_summary(extracted_text),
            'contactInfo': extract_contact_info(extracted_text),
            'skills': extract_skills(extracted_text),
            'workExperience': extract_work_experience(extracted_text),
            'education': extract_education(extracted_text),
            'certifications': extract_certifications(extracted_text),
            'projects': extract_projects(extracted_text)
        }
        
        logger.info("Successfully parsed resume content")
        return parsed_data
        
    except Exception as e:

        logger.error(f"Resume parsing failed: {str(e)}")
        raise ResumeParsingError(f"Failed to parse resume content: {str(e)}")
    

