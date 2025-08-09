import logging
import os
import urllib.parse
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
ALLOWED_EXTENSIONS = {'pdf', 'docx'}

class ResumeUploadSerializer(serializers.ModelSerializer):
    """Optimized serializer for uploading and creating resume"""
    
    file = serializers.FileField(write_only=True, required=True)

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
        request = self.context.get('request')
        file = validated_data['file']
        file_type = self.context['file_type']

        # Safe filename
        safe_filename = os.path.basename(urllib.parse.unquote(file.name))

        resume = Resume(
            user=request.user,
            file=file,
            original_filename=safe_filename,
            file_type=file_type,
            file_size=file.size
        )

        try:
            extracted_text = extract_text_from_resume(file, file_type)
            resume.extracted_text = extracted_text
            parsed_data = parse_resume_content(extracted_text)

            resume.full_name = parsed_data.get('fullName')
            resume.summary = parsed_data.get('summary')
            resume.contact_info = parsed_data.get('contactInfo') or {}
            resume.skills = parsed_data.get('skills') or []
            resume.work_experience = parsed_data.get('workExperience') or []
            resume.education = parsed_data.get('education') or []
            resume.certifications = parsed_data.get('certifications') or []
            resume.projects = parsed_data.get('projects') or []
            resume.is_parsed = True
            resume.parsed_at = timezone.now()

        except (TextExtractionError, ResumeParsingError) as e:
            logger.warning(f"Processing failed for {file.name}: {e}")
            resume.extracted_text = getattr(resume, 'extracted_text', '') or f"Text extraction failed: {e}"
            resume.parsing_error = str(e)
            resume.is_parsed = False

        except Exception as e:
            logger.error(f"Unexpected error during resume processing: {e}")
            resume.extracted_text = "Processing failed due to an unexpected error."
            resume.parsing_error = f"Unexpected error: {e}"
            resume.is_parsed = False

        resume.save()
        return resume


class ResumeListSerializer(serializers.ModelSerializer):
    """Optimized serializer for listing resumes without large fields"""
    skills_display = serializers.SerializerMethodField()

    class Meta:
        model = Resume
        fields = [
            'id', 'original_filename', 'file_type', 'file_size',
            'full_name', 'contact_email', 'contact_phone',
            'skills_display', 'is_parsed', 'uploaded_at', 'updated_at'
        ]

    def get_skills_display(self, obj):
        if not obj.skills:
            return ""
        skills = obj.skills
        display = ', '.join(skills[:5])
        if len(skills) > 5:
            display += f" (+{len(skills) - 5} more)"
        return display


class ResumeDetailSerializer(serializers.ModelSerializer):
    """Optimized detailed serializer with lazy file URL building"""
    file_url = serializers.SerializerMethodField()

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
        request = self.context.get('request')
        return request.build_absolute_uri(obj.file.url) if obj.file and request else None


class ResumeParseSerializer(serializers.ModelSerializer):
    """Re-parse existing resume with single save"""
    class Meta:
        model = Resume
        fields = [
            'id', 'full_name', 'summary', 'contact_info',
            'skills', 'work_experience', 'education', 'certifications',
            'projects', 'is_parsed', 'parsing_error', 'parsed_at'
        ]
        read_only_fields = fields
    
    def update(self, instance, validated_data):
        if not instance.extracted_text:
            raise serializers.ValidationError("No extracted text available for parsing")
        
        try:
            parsed_data = parse_resume_content(instance.extracted_text)
            instance.full_name = parsed_data.get('fullName')
            instance.summary = parsed_data.get('summary')
            instance.contact_info = parsed_data.get('contactInfo') or {}
            instance.skills = parsed_data.get('skills') or []
            instance.work_experience = parsed_data.get('workExperience') or []
            instance.education = parsed_data.get('education') or []
            instance.certifications = parsed_data.get('certifications') or []
            instance.projects = parsed_data.get('projects') or []
            instance.is_parsed = True
            instance.parsing_error = None
            instance.parsed_at = timezone.now()
        except ResumeParsingError as e:
            instance.is_parsed = False
            instance.parsing_error = str(e)
            raise serializers.ValidationError(f"Parsing failed: {e}")

        instance.save()
        return instance


class ResumeAnalyticsSerializer(serializers.ModelSerializer):
    """Optimized analytics serializer — no repeated .get() calls"""
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
    
    def get_total_skills(self, obj): return len(obj.skills or [])
    def get_total_experience_entries(self, obj): return len(obj.work_experience or [])
    def get_total_education_entries(self, obj): return len(obj.education or [])
    def get_total_certifications(self, obj): return len(obj.certifications or [])
    def get_total_projects(self, obj): return len(obj.projects or [])
    def get_has_contact_info(self, obj):
        ci = obj.contact_info or {}
        return bool(ci.get('email') or ci.get('phone'))

    def get_completion_score(self, obj):
        if not obj.is_parsed:
            return 0
        score_map = [
            bool(obj.full_name),
            bool(obj.summary),
            bool(obj.contact_info and (obj.contact_info.get('email') or obj.contact_info.get('phone'))),
            bool(obj.skills),
            bool(obj.work_experience),
            bool(obj.education),
            bool(obj.certifications),
            bool(obj.projects)
        ]
        return round((sum(score_map) / 8) * 100, 1)
