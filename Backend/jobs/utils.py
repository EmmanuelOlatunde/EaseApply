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
    # Ensure company is at least 3 characters long or set it to empty string
    if not extracted_data["company"] or len(extracted_data["company"]) <= 3:
        extracted_data["company"] = ""

    return extracted_data


def extract_job_title(text: str) -> Optional[str]:
    """Extract job title from any job description text (tech or non-tech)."""
    if not isinstance(text, str):
        return None
    
    text = text.strip()
    if not text:
        return None

    # Explicit title markers
    patterns = [
        r'(?i)\bjob\s*title\s*[:\-]\s*([^\n\r]+?)(?=\s*(?:Company|Location|Employment|About|\n|$))',
        r'(?i)\bposition\s*[:\-]\s*([^\n\r]+?)(?=\s*(?:Company|Location|Employment|About|\n|$))',
        r'(?i)\brole\s*[:\-]\s*([^\n\r]+?)(?=\s*(?:Company|Location|Employment|About|\n|$))',
        r'(?i)\btitle\s*[:\-]\s*([^\n\r]+?)(?=\s*(?:Company|Location|Employment|About|\n|$))',
    ]

    for pattern in patterns:
        try:
            match = re.search(pattern, text)
            if match:
                title = match.group(1).strip()
                # Remove separators and clean up
                title = re.split(r'[-@|]', title)[0].strip()
                if 3 < len(title) < 120:
                    return title
        except Exception:
            continue

    # "Company is hiring a/an XXX" patterns
    try:
        hiring_match = re.search(
            r'\b(?:is hiring|seeks|is seeking|looking for (?:an?|to hire an?))\s+([A-Z][A-Za-z\s/&-]+?)(?:\.|,|\sto\b|\sin\b)',
            text
        )
        if hiring_match:
            clean_title = hiring_match.group(1).strip()
            if 3 < len(clean_title) < 120:
                return clean_title
    except Exception:
        pass

    # Keyword-based extraction from first few lines
    keywords = [
        "manager", "engineer", "specialist", "assistant", "officer", "executive",
        "analyst", "consultant", "teacher", "nurse", "driver", "agent", "technician",
        "developer", "coordinator", "administrator"
    ]
    
    try:
        for line in text.splitlines()[:5]:  # Limit to first 5 lines
            line = line.strip()
            if line and len(line) < 50 and not line.lower().startswith(('about', 'we are', 'location', 'employment')):
                if any(word in line.lower() for word in keywords):
                    clean_title = re.split(r'[@|]|\s+-\s+', line)[0].strip()
                    if 3 < len(clean_title) < 120:
                        return clean_title
    except Exception:
        pass

    return None

def extract_company_name(text: str) -> Optional[str]:
    """Extract company name for both tech and non-tech jobs."""
    if not isinstance(text, str) or not text.strip():
        return None

    stopwords = {
        "remote", "global", "full-time", "part-time", "contract", "job", "role",
        "position", "salary", "location", "team", "department", "division", "group"
    }

    patterns = [
        # Fixed: Make the first pattern more flexible - remove strict end requirement
        r'(?i)\b(?:company|organization|employer)\s*[:\-]\s*([A-Z][A-Za-z0-9&.,\-\s]{2,80}?)(?=\s*\n|\s*$|\s*Location:)',
        r'(?i)\b([A-Z][A-Za-z0-9&.,\-\s]{2,80})\s+(?:is\s+hiring|seeks|is\s+looking|invites\sapplications|is\s+on\s+the\s+lookout)',
        r'(?i)(?:at|with|for|@)\s*([A-Z][A-Za-z0-9&.\-]+(?:\s+[A-Z][A-Za-z0-9&.\-]+)*)',
        r'(?i)\b(?:join|work\s+at)\s+([A-Z][A-Za-z0-9&.,\-\s]{2,80})[\'’]?(?:\s+team|\s+company|$)',
    ]

    for pattern in patterns:
        try:
            match = re.search(pattern, text)
            if match:
                company = match.group(1).strip()

                # ✅ Reject pure stopwords, keep real names
                if company.lower() in stopwords:
                    continue

                # ✅ Reject phrases that just contain "company"
                if "company" in company.lower():
                    continue

                # ✅ Reject very short fragments (likely extraction errors)
                if len(company) < 3:
                    continue

                # ✅ Validate it looks like a real company name
                if 3 <= len(company) <= 60 and re.search(r'[A-Za-z]', company):
                    return company
        except Exception:
            continue

    return None


def extract_location(text: str) -> Optional[str]:
    """Extract location (supports city/state/country and remote)."""
    if not isinstance(text, str) or not text.strip():
        return None

    # First, check for an explicit "Location:" tag
    try:
        # This pattern looks for "Location:" and captures the rest of the line
        match = re.search(r'(?i)\bLocation\s*:\s*(.*)', text)
        if match:
            location = match.group(1).strip()
            # Check if the extracted part is just the word remote
            if 'remote' in location.lower():
                return "Remote"
            if 3 < len(location) < 100:
                return location
    except Exception:
        pass

    
    pattern = r'(?i)^\s*Location\s*:\s*(.+)'
    try:
        match = re.search(pattern, text, re.MULTILINE)
        if match:
            location_detail = match.group(1).strip()
            if location_detail: # Ensure it's not an empty string
                return location_detail
    except Exception:
        pass

    # If the above fails, check for the word "remote" anywhere
    try:
        if re.search(r'\b(remote|work from home|anywhere)\b', text, re.IGNORECASE):
            return "Remote"
    except Exception:
        pass
    
    # Add your other, more complex patterns here as a fallback
    # ...

    return None
   #return None


def extract_job_type(text_lower: str) -> str:
    """Extract job type from text"""
    if not isinstance(text_lower, str):
        return 'unknown'
    
    try:
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
    except Exception:
        pass
    
    return 'unknown'


def extract_salary(text: str) -> Optional[str]:
    """Extract salary (hourly, monthly, yearly, or ranges)."""
    if not isinstance(text, str):
        return None
    
    if not text.strip():
        return None

    # Limit to first 10 lines for better performance
    text = '\n'.join(text.splitlines()[:10]).strip()

    patterns = [
        r'(?i)(?:salary|compensation|pay)\s*(?:range)?\s*[:\-]?\s*([$\€\£\₦\¥\₹]\s?\d[\d,]+(?:k)?(?:\s*[–-]\s*[$\€\£\₦\¥\₹]?\s?\d[\d,]+(?:k)?)?(?:\s*(?:per\s*(?:hour|week|month|year)|annually|/year|/hour|/month))?)',
        r'([$\€\£\₦\¥\₹]\s?\d[\d,]+(?:k)?(?:\s*[–-]\s*[$\€\£\₦\¥\₹]?\s?\d[\d,]+(?:k)?)?(?:\s*(?:per\s*(?:hour|week|month|year)|annually|/year|/hour|/month))?)',
        r'(\d+\s*(?:k|K)\s*[-–]\s*\d+\s*(?:k|K))',
        r'([$\€\£\₦\¥\₹]\s?\d+(?:\.\d{1,2})?\s*/?(?:hour|week|month|year|annum))',
    ]

    for pattern in patterns:
        try:
            match = re.search(pattern, text)
            if match:
                salary = match.group(1).strip() if match.lastindex else match.group(0).strip()
                if 4 <= len(salary) <= 100 and re.search(r'\d', salary):
                    return salary
        except Exception:
            continue

    return None


def extract_requirements(text: str) -> Optional[str]:
    """Extract requirements section from text"""
    if not isinstance(text, str):
        return None
    
    if not text.strip():
        return None

    patterns = [
        r'(?i)(?:requirements?|qualifications?|must have):(.*?)(?:\n\n|\n[A-Z]|$)',
        r'(?i)(?:you should have|you need|required skills?|minimum requirements?):(.*?)(?:\n\n|\n[A-Z]|$)',
        r'(?i)(?:requirements?|qualifications?|must have)[:\-]?\s*\n(.*?)(?:\n\n|\n[A-Z]|$)',
        r'(?i)(?:Requirements?|Qualifications?|What you\'ll need)[:\s\n]+(.*?)(?=\n\s*(?:Preferred|Perks|Benefits|Responsibilities|About Us|To Apply|$))'
    ]
    
    for pattern in patterns:
        try:
            match = re.search(pattern, text, re.DOTALL)
            if match:
                requirements = match.group(1).strip()
                if len(requirements) > 10:
                    return requirements
        except Exception:
            continue
    
    return None


def extract_skills(text: str) -> Optional[str]:
    """
    Extracts a wide range of skills (soft, hard, and domain-specific)
    from job descriptions for any industry.
    """
    if not isinstance(text, str):
        return None
    
    if not text.strip():
        return None

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
        try:
            pattern = r'\b' + re.escape(skill) + r'\b'
            if re.search(pattern, text, re.IGNORECASE):
                # Normalize skill name capitalization
                found_skills.add(skill.strip())
        except Exception:
            continue

    # Sort alphabetically for consistency
    if found_skills:
        return ', '.join(sorted(found_skills, key=str.lower))

    return None


def extract_experience_level(text_lower: str) -> Optional[str]:
    """Extract experience level from text"""
    if not isinstance(text_lower, str):
        return None
    
    if not text_lower.strip():
        return None

    try:
        if re.search(r'\b(?:senior|lead|principal|architect)\b', text_lower):
            return 'Senior'
        elif re.search(r'\b(?:junior|entry\s*level|graduate|new\s*grad)\b', text_lower):
            return 'Junior'
        elif re.search(r'\b(?:mid\s*level|intermediate|experienced)\b', text_lower):
            return 'Mid-level'
        elif re.search(r'\b(?:intern|internship)\b', text_lower):
            return 'Internship'
        
        # Check for years of experience
        years_match = re.search(r'(\d+)\s*(?:\+|\-)?\s*(?:years?|yrs?)\b', text_lower)
        if years_match:
            try:
                years = int(years_match.group(1))
                if years <= 2:
                    return 'Junior'
                elif years <= 5:
                    return 'Mid-level'
                else:
                    return 'Senior'
            except ValueError:
                pass
    except Exception:
        pass
    
    return None