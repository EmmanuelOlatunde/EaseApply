from rest_framework import serializers
from jobs.models import JobDescription
from resumes.models import Resume

class CoverLetterGenerateSerializer(serializers.Serializer):
    """Serializer for cover letter generation request"""
    
    job_id = serializers.IntegerField(
        min_value=1, 
        required=False, 
        allow_null=True,
        help_text="ID of the job description (optional, will use latest if not provided)"
    )
    resume_id = serializers.IntegerField(
        min_value=1, 
        required=False, 
        allow_null=True,
        help_text="ID of the resume (optional, will use latest if not provided)"
    )
    
    def validate_job_id(self, value):
        """Validate that job exists and belongs to authenticated user (only if provided)"""
        if value is None:
            return value  # skip validation if not provided
        
        user = self.context['request'].user
        if not JobDescription.objects.filter(id=value, user=user).exists():
            raise serializers.ValidationError(
                "Job description not found or you don't have permission to access it."
            )
        return value
    
    def validate_resume_id(self, value):
        """Validate that resume exists and belongs to authenticated user (only if provided)"""
        if value is None:
            return value  # skip validation if not provided
        
        user = self.context['request'].user
        if not Resume.objects.filter(id=value, user=user).exists():
            raise serializers.ValidationError(
                "Resume not found or you don't have permission to access it."
            )
        return value
    
    def validate(self, attrs):
        """Additional cross-field validation (only if both IDs provided)"""
        user = self.context['request'].user
        
        job_id = attrs.get('job_id')
        resume_id = attrs.get('resume_id')

        # Only validate ownership if both IDs are present
        if job_id and resume_id:
            job = JobDescription.objects.get(id=job_id)
            resume = Resume.objects.get(id=resume_id)

            if job.user != user or resume.user != user:
                raise serializers.ValidationError(
                    "Both job description and resume must belong to the authenticated user."
                )

            # Check if resume has extracted text
            if not resume.extracted_text or resume.extracted_text.strip() == '':
                raise serializers.ValidationError(
                    "Resume must have extracted text content for analysis."
                )

        return attrs


        
class CoverLetterResponseSerializer(serializers.Serializer):
    """Serializer for cover letter generation response"""
    
    success = serializers.BooleanField()
    cover_letter = serializers.CharField(allow_blank=True)
    analysis_id = serializers.IntegerField(required=False)
    metadata = serializers.DictField(required=False)
    message = serializers.CharField(required=False)