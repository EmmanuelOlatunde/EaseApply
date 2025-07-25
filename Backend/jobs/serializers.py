from rest_framework import serializers
from .models import JobDescription
from .utils import extract_text_from_document, extract_job_details
from django.core.exceptions import ValidationError
from django.utils.text import get_valid_filename
import os

class JobDescriptionSerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField(read_only=True)
    created_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)
    document_name = serializers.SerializerMethodField()

    class Meta:
        model = JobDescription
        fields = [
            'id',
            'user',
            'raw_content',
            'document',
            'document_name',
            'title',
            'company',
            'location',
            'job_type',
            'salary_range',
            'requirements',
            'skills_required',
            'experience_level',
            'is_processed',
            'processing_notes',
            'created_at',
            'updated_at',
            'is_active'
        ]
        read_only_fields = [
            'id', 'user', 'created_at', 'updated_at', 'is_processed', 
            'processing_notes', 'document_name'
        ]

    def get_document_name(self, obj):
        if obj.document:
            return obj.document.name.split('/')[-1]  # Return just filename
        return None
    
    def validate_document(self, value):
        # Check for path traversal in filename
        filename = value.name
        # Normalize filename to prevent path traversal
        sanitized_filename = os.path.basename(get_valid_filename(filename))
        if filename != sanitized_filename:
            raise ValidationError('Unsupported file type: Invalid filename.')
        
        # Validate file extension
        allowed_extensions = ['pdf', 'doc', 'docx']
        ext = os.path.splitext(filename)[1].lower().lstrip('.')
        if ext not in allowed_extensions:
            raise ValidationError('Unsupported file type: Only PDF, DOC, and DOCX are allowed.')
        
        # Check if file is empty
        if value.size == 0:
            raise ValidationError('The submitted file is empty.')
        
        return value
    
    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        
        # Extract job details
        extracted = extract_job_details(validated_data.get('raw_content', ''))
        validated_data.update(extracted)
        
        ## ✅ Truncate after extraction
        for field in ['title', 'company', 'location']:
            value = validated_data.get(field)
            if value:
                validated_data[field] = value[:200]
        
        return super().create(validated_data)



class JobDescriptionUploadSerializer(serializers.ModelSerializer):
    """Serializer for uploading job descriptions via document or text"""
    document = serializers.FileField(required=False, allow_null=True)
    raw_content = serializers.CharField(required=False, allow_blank=True)

    class Meta:
        model = JobDescription
        fields = [
            'raw_content',
            'document',
            'is_active'
        ]

    def validate(self, data):
        document = data.get('document')
        raw_content = data.get('raw_content', '').strip()

        # Must provide either document or raw_content
        if not document and not raw_content:
            raise serializers.ValidationError(
                "Either upload a document or provide job description text."
            )

        # Validate document type if provided
        if document:
            allowed_extensions = ['pdf', 'docx', 'doc', 'txt']
            file_extension = document.name.lower().split('.')[-1]
            if file_extension not in allowed_extensions:
                raise serializers.ValidationError(
                    f"Unsupported file type. Allowed types: {', '.join(allowed_extensions)}"
                )

        return data

    def create(self, validated_data):
        document = validated_data.get('document')
        raw_content = validated_data.get('raw_content', '').strip()

        # Extract text from document if provided
        if document:
            try:
                extracted_text = extract_text_from_document(document)
                if not raw_content:  # Use extracted text if no raw_content provided
                    raw_content = extracted_text
                else:  # Append extracted text to provided content
                    raw_content = f"{raw_content}\n\n--- From Document ---\n{extracted_text}"
            except ValueError as e:
                raise serializers.ValidationError(f"Document processing error: {str(e)}")

        # Create job description with raw content
        job_description = JobDescription.objects.create(
            user=self.context['request'].user,
            raw_content=raw_content,
            document=document,
            is_active=validated_data.get('is_active', True)
        )

        # Extract job details from raw content
        try:
            extracted_details = extract_job_details(raw_content)
            
            # Update job description with extracted details
            for field, value in extracted_details.items():
                if value:  # Only set non-empty values
                    setattr(job_description, field, value)
            
            job_description.is_processed = True
            job_description.processing_notes = "Successfully extracted job details"
            job_description.save()

        except Exception as e:
            job_description.is_processed = False
            job_description.processing_notes = f"Error extracting details: {str(e)}"
            job_description.save()

        return job_description


class JobDescriptionListSerializer(serializers.ModelSerializer):
    """Simplified serializer for listing job descriptions"""
    document_name = serializers.SerializerMethodField()
    
    class Meta:
        model = JobDescription
        fields = [
            'id',
            'title',
            'company',
            'location',
            'job_type',
            'document_name',
            'is_processed',
            'created_at',
            'is_active'
        ]

    def get_document_name(self, obj):
        if obj.document:
            return obj.document.name.split('/')[-1]
        return None
    