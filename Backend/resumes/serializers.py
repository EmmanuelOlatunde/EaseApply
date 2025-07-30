import logging
from django.utils import timezone
from rest_framework import serializers
from django.core.files.uploadedfile import UploadedFile
from .models import Resume
from .utils import (
    extract_text_from_resume, 
    validate_resume_file, 
    parse_resume_content,
    TextExtractionError,
    ResumeParsingError
)

logger = logging.getLogger(__name__)

class ResumeUploadSerializer(serializers.ModelSerializer):
    """Serializer for uploading and creating resume with text extraction and parsing"""
    
    file = serializers.FileField(write_only=True, required=True)
    extracted_text = serializers.CharField(read_only=True)
    full_name = serializers.CharField(read_only=True)
    summary = serializers.CharField(read_only=True)
    contact_info = serializers.JSONField(read_only=True)
    skills = serializers.ListField(read_only=True)
    work_experience = serializers.ListField(read_only=True)
    education = serializers.ListField(read_only=True)
    certifications = serializers.ListField(read_only=True)
    projects = serializers.ListField(read_only=True)
    is_parsed = serializers.BooleanField(read_only=True)
    parsing_error = serializers.CharField(read_only=True)
    
    class Meta:
        model = Resume
        fields = [
            'id', 'file', 'original_filename', 'file_type', 
            'extracted_text', 'full_name', 'summary', 'contact_info',
            'skills', 'work_experience', 'education', 'certifications',
            'projects', 'is_parsed', 'parsing_error', 'file_size', 
            'uploaded_at', 'parsed_at'
        ]
        read_only_fields = [
            'id', 'original_filename', 'file_type', 'extracted_text',
            'full_name', 'summary', 'contact_info', 'skills',
            'work_experience', 'education', 'certifications', 'projects',
            'is_parsed', 'parsing_error', 'file_size', 'uploaded_at',
            'parsed_at'
        ]
    
    def validate_file(self, file: UploadedFile):
        file_type, is_valid = validate_resume_file(file)
        if not is_valid:
            raise serializers.ValidationError(
                "Invalid file. Please upload a PDF or DOCX file under 10MB."
            )
        self.context['file_type'] = file_type
        return file
    
    def create(self, validated_data):
        """Create resume instance with automatic text extraction and parsing"""
        request = self.context.get('request')
        file = validated_data['file']
        file_type = self.context.get('file_type')
        
        # Create resume instance
        resume = Resume(
            user=request.user,
            file=file,
            original_filename=file.name,
            file_type=file_type,
            file_size=file.size
        )
        
        # Extract text from the file
        try:
            extracted_text = extract_text_from_resume(file, file_type)
            resume.extracted_text = extracted_text
            logger.info(f"Successfully extracted text from {file.name} for user {request.user.id}")
            
            # Parse the extracted text into structured data
            try:
                parsed_data = parse_resume_content(extracted_text)
                
                # Update resume with parsed data
                resume.full_name = parsed_data.get('fullName')
                resume.summary = parsed_data.get('summary')
                resume.contact_info = parsed_data.get('contactInfo', {})
                resume.skills = parsed_data.get('skills', [])
                resume.work_experience = parsed_data.get('workExperience', [])
                resume.education = parsed_data.get('education', [])
                resume.certifications = parsed_data.get('certifications', [])
                resume.projects = parsed_data.get('projects', [])
                resume.is_parsed = True
                resume.parsed_at = timezone.now()
                
                logger.info(f"Successfully parsed resume content for {file.name} for user {request.user.id}")
                
            except ResumeParsingError as e:
                logger.warning(f"Resume parsing failed for {file.name}: {str(e)}")
                resume.parsing_error = str(e)
                resume.is_parsed = False
                
        except TextExtractionError as e:
            logger.warning(f"Text extraction failed for {file.name}: {str(e)}")
            resume.extracted_text = f"Text extraction failed: {str(e)}"
            resume.parsing_error = f"Text extraction failed: {str(e)}"
            resume.is_parsed = False
        except Exception as e:
            logger.error(f"Unexpected error during text extraction for {file.name}: {str(e)}")
            resume.extracted_text = "Text extraction failed due to an unexpected error."
            resume.parsing_error = f"Unexpected error: {str(e)}"
            resume.is_parsed = False
        
        resume.save()
        return resume

class ResumeListSerializer(serializers.ModelSerializer):
    """Serializer for listing resumes (without full text but with key parsed data)"""
    
    contact_email = serializers.CharField(read_only=True)
    contact_phone = serializers.CharField(read_only=True)
    skills_display = serializers.SerializerMethodField()
    
    class Meta:
        model = Resume
        fields = [
            'id', 'original_filename', 'file_type', 'file_size',
            'full_name', 'contact_email', 'contact_phone',
            'skills_display', 'is_parsed', 'uploaded_at', 'updated_at'
        ]
    
    def get_skills_display(self, obj):
        """Get first 5 skills as comma-separated string"""
        if obj.skills:
            display_skills = obj.skills[:5]  # Show only first 5 skills
            result = ', '.join(display_skills)
            if len(obj.skills) > 5:
                result += f" (+{len(obj.skills) - 5} more)"
            return result
        return ""

class ResumeDetailSerializer(serializers.ModelSerializer):
    """Serializer for detailed resume view (with all parsed data)"""
    
    file_url = serializers.SerializerMethodField()
    contact_email = serializers.CharField(read_only=True)
    contact_phone = serializers.CharField(read_only=True)
    contact_linkedin = serializers.CharField(read_only=True)
    
    class Meta:
        model = Resume
        fields = [
            'id', 'original_filename', 'file_type', 'file_size',
            'extracted_text', 'full_name', 'summary', 'contact_info',
            'contact_email', 'contact_phone', 'contact_linkedin',
            'skills', 'work_experience', 'education', 'certifications',
            'projects', 'is_parsed', 'parsing_error', 'uploaded_at',
            'updated_at', 'parsed_at', 'file_url'
        ]
    
    def get_file_url(self, obj):
        """Get the file URL"""
        request = self.context.get('request')
        if obj.file and request:
            return request.build_absolute_uri(obj.file.url)
        return None

class ResumeParseSerializer(serializers.ModelSerializer):
    """Serializer for re-parsing existing resume"""
    
    class Meta:
        model = Resume
        fields = [
            'id', 'full_name', 'summary', 'contact_info',
            'skills', 'work_experience', 'education', 'certifications',
            'projects', 'is_parsed', 'parsing_error', 'parsed_at'
        ]
        read_only_fields = fields
    
    def update(self, instance, validated_data):
        """Re-parse the resume content"""
        if not instance.extracted_text:
            raise serializers.ValidationError("No extracted text available for parsing")
        
        try:
            parsed_data = parse_resume_content(instance.extracted_text)
            
            # Update instance with parsed data
            instance.full_name = parsed_data.get('fullName')
            instance.summary = parsed_data.get('summary')
            instance.contact_info = parsed_data.get('contactInfo', {})
            instance.skills = parsed_data.get('skills', [])
            instance.work_experience = parsed_data.get('workExperience', [])
            instance.education = parsed_data.get('education', [])
            instance.certifications = parsed_data.get('certifications', [])
            instance.projects = parsed_data.get('projects', [])
            instance.is_parsed = True
            instance.parsing_error = None
            instance.parsed_at = timezone.now()
            
            instance.save()
            logger.info(f"Successfully re-parsed resume {instance.id}")
            
        except ResumeParsingError as e:
            instance.parsing_error = str(e)
            instance.is_parsed = False
            instance.save()
            logger.warning(f"Resume re-parsing failed for {instance.id}: {str(e)}")
            raise serializers.ValidationError(f"Parsing failed: {str(e)}")
        
        return instance

class ContactInfoSerializer(serializers.Serializer):
    """Serializer for contact information display"""
    email = serializers.CharField(required=False, allow_blank=True)
    phone = serializers.CharField(required=False, allow_blank=True)
    address = serializers.CharField(required=False, allow_blank=True)
    linkedin = serializers.CharField(required=False, allow_blank=True)
    github = serializers.CharField(required=False, allow_blank=True)

class WorkExperienceSerializer(serializers.Serializer):
    """Serializer for work experience entries"""
    title = serializers.CharField(required=False, allow_blank=True)
    company = serializers.CharField(required=False, allow_blank=True)
    duration = serializers.CharField(required=False, allow_blank=True)
    description = serializers.ListField(
        child=serializers.CharField(),
        required=False,
        allow_empty=True
    )

class EducationSerializer(serializers.Serializer):
    """Serializer for education entries"""
    degree = serializers.CharField(required=False, allow_blank=True)
    institution = serializers.CharField(required=False, allow_blank=True)
    year = serializers.CharField(required=False, allow_blank=True)

class ProjectSerializer(serializers.Serializer):
    """Serializer for project entries"""
    name = serializers.CharField(required=False, allow_blank=True)
    description = serializers.ListField(
        child=serializers.CharField(),
        required=False,
        allow_empty=True
    )

class ResumeAnalyticsSerializer(serializers.ModelSerializer):
    """Serializer for resume analytics and statistics"""
    
    total_skills = serializers.SerializerMethodField()
    total_experience_entries = serializers.SerializerMethodField()
    total_education_entries = serializers.SerializerMethodField()
    total_certifications = serializers.SerializerMethodField()
    total_projects = serializers.SerializerMethodField()
    has_contact_info = serializers.SerializerMethodField()
    completion_score = serializers.SerializerMethodField()
    
    class Meta:
        model = Resume
        fields = [
            'id', 'original_filename', 'full_name', 'is_parsed',
            'total_skills', 'total_experience_entries', 'total_education_entries',
            'total_certifications', 'total_projects', 'has_contact_info',
            'completion_score', 'uploaded_at'
        ]
    
    def get_total_skills(self, obj):
        return len(obj.skills) if obj.skills else 0
    
    def get_total_experience_entries(self, obj):
        return len(obj.work_experience) if obj.work_experience else 0
    
    def get_total_education_entries(self, obj):
        return len(obj.education) if obj.education else 0
    
    def get_total_certifications(self, obj):
        return len(obj.certifications) if obj.certifications else 0
    
    def get_total_projects(self, obj):
        return len(obj.projects) if obj.projects else 0
    
    def get_has_contact_info(self, obj):
        if not obj.contact_info:
            return False
        return bool(obj.contact_info.get('email') or obj.contact_info.get('phone'))
    
    def get_completion_score(self, obj):
        """Calculate completion score based on available sections"""
        if not obj.is_parsed:
            return 0
        
        score = 0
        max_score = 8
        
        # Check each section
        if obj.full_name:
            score += 1
        if obj.summary:
            score += 1
        if obj.contact_info and (obj.contact_info.get('email') or obj.contact_info.get('phone')):
            score += 1
        if obj.skills:
            score += 1
        if obj.work_experience:
            score += 1
        if obj.education:
            score += 1
        if obj.certifications:
            score += 1
        if obj.projects:
            score += 1
        
        return round((score / max_score) * 100, 1)