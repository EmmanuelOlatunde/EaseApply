import logging
from rest_framework import serializers
from django.core.files.uploadedfile import UploadedFile
from .models import Resume
from .utils import extract_text_from_resume, validate_resume_file, TextExtractionError

logger = logging.getLogger(__name__)

class ResumeUploadSerializer(serializers.ModelSerializer):
    """Serializer for uploading and creating resume with text extraction"""
    
    file = serializers.FileField(write_only=True, required=True)
    extracted_text = serializers.CharField(read_only=True)
    
    class Meta:
        model = Resume
        fields = [
            'id', 'file', 'original_filename', 'file_type', 
            'extracted_text', 'file_size', 'uploaded_at'
        ]
        read_only_fields = [
            'id', 'original_filename', 'file_type', 
            'extracted_text', 'file_size', 'uploaded_at'
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
        """Create resume instance with automatic text extraction"""
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
        except TextExtractionError as e:
            logger.warning(f"Text extraction failed for {file.name}: {str(e)}")
            resume.extracted_text = f"Text extraction failed: {str(e)}"
        except Exception as e:
            logger.error(f"Unexpected error during text extraction for {file.name}: {str(e)}")
            resume.extracted_text = "Text extraction failed due to an unexpected error."
        
        resume.save()
        return resume

class ResumeListSerializer(serializers.ModelSerializer):
    """Serializer for listing resumes (without full text)"""
    
    class Meta:
        model = Resume
        fields = [
            'id', 'original_filename', 'file_type', 
            'file_size', 'uploaded_at', 'updated_at'
        ]

class ResumeDetailSerializer(serializers.ModelSerializer):
    """Serializer for detailed resume view (with extracted text)"""
    
    file_url = serializers.SerializerMethodField()
    
    class Meta:
        model = Resume
        fields = [
            'id', 'original_filename', 'file_type', 'file_size',
            'extracted_text', 'uploaded_at', 'updated_at', 'file_url'
        ]
    
    def get_file_url(self, obj):
        """Get the file URL"""
        request = self.context.get('request')
        if obj.file and request:
            return request.build_absolute_uri(obj.file.url)
        return None