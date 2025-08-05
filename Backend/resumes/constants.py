# File validation constants
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
ALLOWED_EXTENSIONS = ['pdf', 'docx']
ALLOWED_MIME_TYPES = [
    'application/pdf',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    'application/msword'
]

# Parsing constants
MAX_RESUME_TEXT_LENGTH = 50000  # Maximum characters in extracted text
MIN_RESUME_TEXT_LENGTH = 50     # Minimum characters for valid resume

# Skills extraction
COMMON_TECHNICAL_SKILLS = [
    'Python', 'Java', 'JavaScript', 'React', 'Django', 'Flask',
    'Node.js', 'SQL', 'PostgreSQL', 'MySQL', 'MongoDB', 'AWS',
    'Docker', 'Kubernetes', 'Git', 'Linux', 'HTML', 'CSS'
]

# Section keywords for parsing
SECTION_KEYWORDS = {
    'summary': [
        'summary', 'professional summary', 'executive summary',
        'profile', 'professional profile', 'career summary',
        'objective', 'career objective'
    ],
    'experience': [
        'experience', 'professional experience', 'work experience',
        'employment', 'work history', 'career history'
    ],
    'education': [
        'education', 'academic background', 'qualifications',
        'academic qualifications'
    ],
    'skills': [
        'skills', 'technical skills', 'core competencies',
        'technologies', 'technical competencies'
    ],
    'projects': [
        'projects', 'personal projects', 'key projects',
        'notable projects'
    ],
    'certifications': [
        'certifications', 'certificates', 'professional certifications',
        'licenses'
    ]
}
