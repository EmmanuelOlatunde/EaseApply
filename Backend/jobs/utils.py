import re
import PyPDF2
import docx
from django.core.files.uploadedfile import InMemoryUploadedFile
from typing import Dict, Optional


def extract_text_from_document(document: InMemoryUploadedFile) -> str:
    """Extract text from uploaded document (PDF, DOCX, TXT)"""
    
    file_extension = document.name.lower().split('.')[-1]
    text_content = ""
    
    try:
        if file_extension == 'pdf':
            text_content = extract_from_pdf(document)
        elif file_extension in ['docx', 'doc']:
            text_content = extract_from_docx(document)
        elif file_extension == 'txt':
            text_content = document.read().decode('utf-8')
        else:
            raise ValueError(f"Unsupported file type: {file_extension}")
            
    except Exception as e:
        raise ValueError(f"Error extracting text from document: {str(e)}")
    
    return text_content


def extract_from_pdf(document: InMemoryUploadedFile) -> str:
    """Extract text from PDF file"""
    text = ""
    try:
        pdf_reader = PyPDF2.PdfReader(document)
        for page in pdf_reader.pages:
            text += page.extract_text() + "\n"
    except Exception as e:
        raise ValueError(f"Error reading PDF: {str(e)}")
    
    return text


def extract_from_docx(document: InMemoryUploadedFile) -> str:
    """Extract text from DOCX file"""
    try:
        doc = docx.Document(document)
        text = ""
        for paragraph in doc.paragraphs:
            text += paragraph.text + "\n"
    except Exception as e:
        raise ValueError(f"Error reading DOCX: {str(e)}")
    
    return text


def extract_job_details(raw_content: str) -> Dict[str, Optional[str]]:
    """
    Extract job details from raw job description text using regex patterns
    """
    
    # Clean and normalize text
    text = re.sub(r'\s+', ' ', raw_content.strip())
    text_lower = text.lower()
    
    extracted_data = {
        'title': extract_job_title(text),
        'company': extract_company_name(text),
        'location': extract_location(text),
        'job_type': extract_job_type(text_lower),
        'salary_range': extract_salary(text),
        'requirements': extract_requirements(text),
        'skills_required': extract_skills(text),
        'experience_level': extract_experience_level(text_lower),
    }
    
    return extracted_data


def extract_job_title(text: str) -> Optional[str]:
    """Extract job title from text"""
    patterns = [
        r'(?:job title|position|role):\s*([^\n\r]+)',
        r'(?:title):\s*([^\n\r]+)',
        r'^([^\n\r]+?)(?:\s*-\s*|\s*at\s*|\s*@\s*)',  # First line with separator
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
        if match:
            title = match.group(1).strip()
            if len(title) > 3 and len(title) < 100:  # Reasonable title length
                return title
    
    # Fallback: first meaningful line
    lines = text.split('\n')
    for line in lines[:3]:  # Check first 3 lines
        line = line.strip()
        if len(line) > 5 and len(line) < 100 and not line.lower().startswith(('job', 'about', 'we are')):
            return line
    
    return None


def extract_company_name(text: str) -> Optional[str]:
    """Extract company name from text"""
    patterns = [
        r'(?:company|organization|employer):\s*([^\n\r]+)',
        r'(?:at|@)\s+([A-Z][a-zA-Z\s&.,]+?)(?:\s*-|\s*\n|\s*is\s)',
        r'([A-Z][a-zA-Z\s&.,]{2,30})\s+(?:is looking|seeks|hiring)',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            company = match.group(1).strip()
            if len(company) > 2 and len(company) < 50:
                return company
    
    return None


def extract_location(text: str) -> Optional[str]:
    """Extract location from text"""
    patterns = [
        r'(?:location|based in|office in):\s*([^\n\r]+)',
        r'(?:remote|hybrid|on-site).*?(?:in|at)\s+([A-Za-z\s,]+?)(?:\n|,|\.|$)',
        r'([A-Za-z\s]+,\s*[A-Z]{2}(?:\s+\d{5})?)',  # City, State format
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            location = match.group(1).strip()
            if len(location) > 3 and len(location) < 100:
                return location
    
    # Check for remote keywords
    if re.search(r'\b(?:remote|work from home|wfh)\b', text, re.IGNORECASE):
        return "Remote"
    
    return None


def extract_job_type(text_lower: str) -> str:
    """Extract job type from text"""
    if re.search(r'\b(?:full.?time|full time)\b', text_lower):
        return 'full_time'
    elif re.search(r'\b(?:part.?time|part time)\b', text_lower):
        return 'part_time'
    elif re.search(r'\b(?:contract|contractor|freelance)\b', text_lower):
        return 'contract'
    elif re.search(r'\b(?:intern|internship)\b', text_lower):
        return 'internship'
    elif re.search(r'\b(?:remote|work from home)\b', text_lower):
        return 'remote'
    
    return 'unknown'


def extract_salary(text: str) -> Optional[str]:
    """Extract salary information from text"""
    patterns = [
        r'(?:salary|compensation|pay):\s*([^\n\r]+)',
        r'\$[\d,]+(?:\s*-\s*\$[\d,]+)?(?:\s*per\s*year|\s*annually|\s*/year)?',
        r'[\d,]+k?\s*-\s*[\d,]+k?\s*(?:per year|annually|/year)',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            salary = match.group(0).strip()
            if len(salary) > 3:
                return salary
    
    return None


def extract_requirements(text: str) -> Optional[str]:
    """Extract requirements section from text"""
    patterns = [
        r'(?:requirements?|qualifications?|must have):(.*?)(?:\n\n|\n[A-Z]|$)',
        r'(?:you should have|you need|required skills?|minimum requirements?):(.*?)(?:\n\n|\n[A-Z]|$)',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
        if match:
            requirements = match.group(1).strip()
            if len(requirements) > 10:
                return requirements
    
    return None


def extract_skills(text: str) -> Optional[str]:
    """Extract skills from text"""
    # Common skill patterns
    skill_patterns = [
        r'(?:skills?|technologies?|tools?):\s*([^\n\r]+)',
        r'(?:experience with|proficiency in|knowledge of):\s*([^\n\r]+)',
    ]
    
    skills = []
    for pattern in skill_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        skills.extend(matches)
    
    # Look for common tech skills
    tech_skills = re.findall(
        r'\b(?:Python|Java|JavaScript|React|Django|SQL|AWS|Docker|Git|HTML|CSS|Node\.js|Angular|Vue\.js)\b',
        text, re.IGNORECASE
    )
    
    all_skills = skills + tech_skills
    if all_skills:
        return ', '.join(set(all_skills))
    
    return None


def extract_experience_level(text_lower: str) -> Optional[str]:
    """Extract experience level from text"""
    if re.search(r'\b(?:senior|lead|principal|architect)\b', text_lower):
        return 'Senior'
    elif re.search(r'\b(?:junior|entry.level|graduate|new grad)\b', text_lower):
        return 'Junior'
    elif re.search(r'\b(?:mid.level|intermediate|experienced)\b', text_lower):
        return 'Mid-level'
    elif re.search(r'\b(?:intern|internship)\b', text_lower):
        return 'Internship'
    
    # Check for years of experience
    years_match = re.search(r'(\d+)\s*(?:\+|\-)?(?:years?|yrs?)', text_lower)
    if years_match:
        years = int(years_match.group(1))
        if years <= 2:
            return 'Junior'
        elif years <= 5:
            return 'Mid-level'
        else:
            return 'Senior'
    
    return None