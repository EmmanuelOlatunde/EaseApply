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
    """Extract job title from any job description text (tech or non-tech)."""
    text = text.strip()

    # Explicit title markers
    patterns = [
        r'(?i)\bjob\s*title\s*[:\-]\s*([^\n\r]+)',
        r'(?i)\bposition\s*[:\-]\s*([^\n\r]+)',
        r'(?i)\brole\s*[:\-]\s*([^\n\r]+)',
        r'(?i)\btitle\s*[:\-]\s*([^\n\r]+)',
        r'(?i)\bjob\s*title\s*[:\-]\s*([A-Za-z0-9&().,\-\/\s]{3,100}?)(?=\s*(?:Company|Location|Employment|About|\n|$))',
        r'(?i)\bposition\s*[:\-]\s*([A-Za-z0-9&().,\-\/\s]{3,100}?)(?=\s*(?:Company|Location|Employment|About|\n|$))',
    ]


    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            title = re.split(r'[-@|]', match.group(1).strip())[0]
            if 3 < len(title) < 120:
                return title

    # "Company is hiring a/an XXX"
    hiring_match = re.search(
        r'\b(?:is hiring|seeks|is seeking|looking for (?:an?|to hire an?))\s+([A-Z][A-Za-z\s/&-]+?)(?:\.|,|\sto\b|\sin\b)',
        text
    )
    if hiring_match:
        clean_title = hiring_match.group(1).strip()
        if 3 < len(clean_title) < 120:
            return clean_title

    keywords = [
        "manager", "engineer", "specialist", "assistant", "officer", "executive",
        "analyst", "consultant", "teacher", "nurse", "driver", "agent", "technician",
        "developer", "coordinator", "administrator"
    ]
    for line in text.splitlines()[:5]:  # Limit to first 5 lines
        line = line.strip()
        if line and len(line) < 50 and not line.lower().startswith(('about', 'we are', 'location', 'employment')):
            if any(word in line.lower() for word in keywords):
                return re.split(r'[@|]|\s+-\s+', line)[0].strip()

    return None


def extract_company_name(text: str) -> Optional[str]:
    """Extract company name for both tech and non-tech jobs."""

    stopwords = {
        "remote", "global", "full-time", "part-time", "contract", "job", "role",
        "position", "salary", "location", "team", "department", "division", "group"
    }
    patterns = [
        r'(?:company|organization|employer)\s*[:\-]\s*([A-Za-z0-9&.,\s]{2,80})(?=\s*(?:\n|Location|$))',
        r'(?:at|with)\s+([A-Za-z0-9&.,\s]{2,80})(?=\s*(?:\-|\n|is|seeks|hiring|,|$))',
        r'([A-Za-z0-9&.,\s]{2,80})\s+(?:is\s+hiring|seeks|is\s+looking|invites\sapplications)(?!\s*(?:New York|California|London))',
        r'(?:company|organization|employer)\s*[:\-]\s*([A-Za-z0-9&.,\s]{2,80}?)(?=\s*(?:Location|Job|Employment|About|\n|$))',
        r'\bat\s+([A-Za-z0-9&.,\s]{2,80}?)(?=\s*(?:\-|\n|is|seeks|hiring|,|$))',
        r'([A-Za-z0-9&.,\s]{2,80}?)\s+(?:is\s+hiring|seeks|is\s+looking|invites\sapplications)(?!\s*(?:New York|California|London))',
        r'([A-Za-z0-9&.,\s]{2,80}),\s*(?:a|an)\s*(?:tech|healthcare|retail)\s*(?:company|firm|organization)',
        r'\b(?:join|work\s+at)\s+([A-Za-z0-9&.,\s]{2,80})[\'’]?s\s*(?:team|company)'
    ]

    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            company = match.group(1).strip()
            if (
                2 <= len(company) <= 60
                and not any(stop in company.lower() for stop in stopwords)
            ):
                return company

    return None


def extract_location(text: str) -> Optional[str]:
    """Extract location (supports city/state/country and remote)."""
    text = '\n'.join(text.splitlines()[:10]).strip()  # Limit to first 10 lines

    patterns = [
        r'(?:location|based in|office in)\s*[:\-]?\s*([^\n\r,]+,\s*[A-Za-z\s]+)',
        r'([A-Za-z\s]+,\s*[A-Z]{2}(?:\s+\d{5})?)(?!\s*(?:Department|Team|Division))',
        r'\b(?:in|at)\s+([A-Za-z\s]+,\s*[A-Za-z]{2,})',
        r'(?:location|based in|office in)\s*[:\-]?\s*([A-Za-z\s]+,\s*[A-Za-z\s]+)(?=\s*(?:Employment|Job|Salary|About|\n|$))',
        r'(?:location|based in|office in)\s*[:\-]?\s*([A-Za-z\s]{3,50})(?=\s*(?:Employment|Job|Salary|About|\n|$))'
    ]

    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            location = match.group(1).strip()
            if 3 < len(location) < 100:
                return location

    # Remote check
    if re.search(r'\b(remote|work from home|hybrid)\b', text, re.IGNORECASE):
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
    """Extract salary (hourly, monthly, yearly, or ranges)."""
    text = '\n'.join(text.splitlines()[:10]).strip()  # Limit to first 10 lines

    patterns = [
        r'(?:salary|compensation|pay)\s*(?:range)?\s*[:\-]?\s*([$\€\£\₦\¥\₹]\s?\d[\d,]*(?:\.\d{1,2})?(?:\s*[–-]\s*[$\€\£\₦\¥\₹]?\s?\d[\d,]*(?:\.\d{1,2})?)?(?:\s*(?:per\s*(?:hour|week|month|year)|annually|/year|/hour|/month))?)',
        r'([$\€\£\₦\¥\₹]\s?\d[\d,]*(?:\.\d{1,2})?(?:\s*[–-]\s*[$\€\£\₦\¥\₹]?\s?\d[\d,]*(?:\.\d{1,2})?)?(?:\s*(?:per\s*(?:hour|week|month|year)|annually|/year|/hour|/month))?(?!\s*(?:budget|cost|expense)))',
        r'([$\€\£\₦\¥\₹]\s?\d+(?:\.\d{1,2})?\s*/?(?:hour|week|month|year|annum))',
        r'(?:salary|compensation|pay)\s*(?:range)?\s*[:\-]?\s*([$\€\£\₦\¥\₹]\s?\d[\d,]*(?:\.\d{1,2})?(?:\s*[–-]\s*[$\€\£\₦\¥\₹]?\s?\d[\d,]*(?:\.\d{1,2})?)?(?:\s*(?:per\s*(?:hour|week|month|year)|annually|/year|/hour|/month)?)?)(?=\s*(?:About|Key|Responsibilities|\n|$))'
    ]

    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            salary = match.group(1).strip() if match.lastindex else match.group(0).strip()
            if 4 <= len(salary) <= 100 and re.search(r'\d+[1-9]', salary):
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
    """
    Extracts a wide range of skills (soft, hard, and domain-specific)
    from job descriptions for any industry.
    """

    # Expanded keywords by category
    skill_categories = {
        "soft_skills": [
            "communication", "leadership", "teamwork", "collaboration", "critical thinking",
            "problem solving", "analytical", "negotiation", "organization", "presentation",
            "customer service", "adaptability", "creativity", "time management", "multitasking",
            "conflict resolution", "attention to detail", "decision making", "strategic thinking"
        ],
        "business_sales_marketing": [
            "salesforce", "CRM", "HubSpot", "Zoho", "SEO", "SEM", "Google Analytics", 
            "digital marketing", "content strategy", "copywriting", "market research", 
            "lead generation", "B2B sales", "email marketing", "social media marketing",
            "public relations", "brand management"
        ],
        "healthcare": [
            "patient care", "clinical", "EMR", "EHR", "nursing", "phlebotomy",
            "medication administration", "vital signs monitoring", "HIPAA compliance",
            "diagnostic imaging", "surgical assistance", "CPR", "first aid"
        ],
        "education_training": [
            "lesson planning", "curriculum development", "classroom management",
            "student assessment", "educational technology", "mentoring", "tutoring"
        ],
        "finance_hr_admin": [
            "bookkeeping", "QuickBooks", "payroll processing", "financial analysis",
            "budgeting", "forecasting", "tax preparation", "accounts receivable",
            "accounts payable", "HRIS", "recruitment", "employee relations", "compliance"
        ],
        "logistics_operations": [
            "supply chain management", "inventory management", "warehouse operations",
            "fleet management", "logistics planning", "procurement", "order fulfillment",
            "SAP", "Oracle ERP"
        ],
        "tech_it": [
            "Python", "Go", "Java", "JavaScript", "C++", "C#", "Ruby", "PHP", 
            "Django", "FastAPI", "Flask", "Spring Boot", "SQL", "PostgreSQL", "MySQL", "MongoDB",
            "AWS", "Azure", "GCP", "Docker", "Kubernetes", "Terraform", "CI/CD", 
            "Jenkins", "Ansible", "Kafka", "RabbitMQ", "REST API", "GraphQL", "React", "Angular",
            "Vue.js", "HTML", "CSS", "Git", "Linux", "Bash scripting"
        ],
        "project_management": [
            "Agile", "Scrum", "Kanban", "Waterfall", "Jira", "Trello", "Asana",
            "MS Project", "risk management", "stakeholder management"
        ]
    }

    # Combine all into a single searchable list
    all_skills = []
    for category_skills in skill_categories.values():
        all_skills.extend(category_skills)

    # Use a set to avoid duplicates
    found_skills = set()

    # Search with word boundaries to avoid partial matches
    for skill in all_skills:
        pattern = r'\b' + re.escape(skill) + r'\b'
        if re.search(pattern, text, re.IGNORECASE):
            # Normalize skill name capitalization
            found_skills.add(skill.strip())

    # Sort alphabetically for consistency
    if found_skills:
        return ', '.join(sorted(found_skills, key=str.lower))

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