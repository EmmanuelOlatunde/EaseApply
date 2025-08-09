from rest_framework import serializers
from django.core.exceptions import ValidationError
from django.utils.text import get_valid_filename
from .models import JobDescription
from .utils import extract_text_from_document, extract_job_details
import os

ALLOWED_DOC_EXTENSIONS = {'pdf', 'doc', 'docx', 'txt'}
ALLOWED_UPLOAD_EXTENSIONS = {'pdf', 'doc', 'docx'}

class JobDescriptionSerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField(read_only=True)
    created_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)
    document_name = serializers.SerializerMethodField()

    class Meta:
        model = JobDescription
        fields = [
            'id', 'user', 'raw_content', 'document', 'document_name',
            'title', 'company', 'location', 'job_type', 'salary_range',
            'requirements', 'skills_required', 'experience_level',
            'is_processed', 'processing_notes', 'created_at', 'updated_at', 'is_active'
        ]
        read_only_fields = [
            'id', 'user', 'created_at', 'updated_at',
            'is_processed', 'processing_notes', 'document_name'
        ]

    def get_document_name(self, obj):
        return os.path.basename(obj.document.name) if obj.document else None

    def validate_document(self, value):
        filename = value.name
        sanitized_filename = os.path.basename(get_valid_filename(filename))
        if filename != sanitized_filename:
            raise ValidationError('Invalid filename.')

        ext = filename.rsplit('.', 1)[-1].lower()
        if ext not in ALLOWED_UPLOAD_EXTENSIONS:
            raise ValidationError('Only PDF, DOC, and DOCX are allowed.')

        if value.size == 0:
            raise ValidationError('The submitted file is empty.')

        return value

    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        extracted = extract_job_details(validated_data.get('raw_content', ''))

        # Truncate extracted fields to avoid DB overflow
        for field in ('title', 'company', 'location'):
            if extracted.get(field):
                extracted[field] = extracted[field][:200]

        validated_data.update(extracted)
        return super().create(validated_data)


class JobDescriptionUploadSerializer(serializers.ModelSerializer):
    document = serializers.FileField(required=False, allow_null=True)
    raw_content = serializers.CharField(required=False, allow_blank=True)

    class Meta:
        model = JobDescription
        fields = ['raw_content', 'document', 'is_active']

    def validate(self, data):
        doc = data.get('document')
        raw_content = (data.get('raw_content') or '').strip()

        if not doc and not raw_content:
            raise serializers.ValidationError(
                "Either upload a document or provide job description text."
            )

        if doc:
            ext = doc.name.rsplit('.', 1)[-1].lower()
            if ext not in ALLOWED_DOC_EXTENSIONS:
                raise serializers.ValidationError(
                    f"Unsupported file type. Allowed: {', '.join(ALLOWED_DOC_EXTENSIONS)}"
                )

        return data

    def create(self, validated_data):
        doc = validated_data.get('document')
        raw_content = (validated_data.get('raw_content') or '').strip()

        if doc:
            try:
                extracted_text = extract_text_from_document(doc)
                if not raw_content:
                    raw_content = extracted_text
                else:
                    raw_content = f"{raw_content}\n\n--- From Document ---\n{extracted_text}"
            except ValueError as e:
                raise serializers.ValidationError(f"Document processing error: {str(e)}")

        job_description = JobDescription(
            user=self.context['request'].user,
            raw_content=raw_content,
            document=doc,
            is_active=validated_data.get('is_active', True)
        )

        try:
            extracted_details = extract_job_details(raw_content)
            for field, value in extracted_details.items():
                if value:
                    setattr(job_description, field, value)

            job_description.is_processed = True
            job_description.processing_notes = "Successfully extracted job details"
        except Exception as e:
            job_description.is_processed = False
            job_description.processing_notes = f"Error extracting details: {str(e)}"

        job_description.save()
        return job_description


class JobDescriptionListSerializer(serializers.ModelSerializer):
    document_name = serializers.SerializerMethodField()

    class Meta:
        model = JobDescription
        fields = [
            'id', 'title', 'company', 'location', 'job_type',
            'document_name', 'is_processed', 'created_at', 'is_active'
        ]

    def get_document_name(self, obj):
        return os.path.basename(obj.document.name) if obj.document else None
