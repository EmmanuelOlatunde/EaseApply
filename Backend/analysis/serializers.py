from rest_framework import serializers
from jobs.models import JobDescription
from resumes.models import Resume

class CoverLetterGenerateSerializer(serializers.Serializer):
    """Serializer for cover letter generation request"""

    job_id = serializers.UUIDField(
        required=False,
        allow_null=True,
        help_text="ID of the job description (optional, will use latest if not provided)"
    )
    resume_id = serializers.UUIDField(
        required=False,
        allow_null=True,
        help_text="ID of the resume (optional, will use latest if not provided)"
    )

    def _get_user_object(self, model, obj_id, user, not_found_msg):
        """Helper: Fetch object with ownership check in one query."""
        try:
            return model.objects.only('id', 'user', 'extracted_text').get(id=obj_id, user=user)
        except model.DoesNotExist:
            raise serializers.ValidationError(not_found_msg)

    def validate(self, attrs):
        """Single-pass validation for job and resume."""
        request = self.context.get('request')
        if not request:
            raise serializers.ValidationError("Request context is required for validation.")

        user = request.user
        job_id = attrs.get('job_id')
        resume_id = attrs.get('resume_id')

        job = resume = None

        # Validate job if provided
        if job_id:
            job = self._get_user_object(
                JobDescription, job_id, user,
                "Job description not found or you don't have permission to access it."
            )

        # Validate resume if provided
        if resume_id:
            resume = self._get_user_object(
                Resume, resume_id, user,
                "Resume not found or you don't have permission to access it."
            )
            if not resume.extracted_text or not resume.extracted_text.strip():
                raise serializers.ValidationError(
                    "Resume must have extracted text content for analysis."
                )

        # If both provided, ensure they belong to same user (already enforced in _get_user_object)
        attrs['job'] = job
        attrs['resume'] = resume
        return attrs


class CoverLetterResponseSerializer(serializers.Serializer):
    success = serializers.BooleanField()
    cover_letter = serializers.CharField(allow_blank=True, required=False)
    analysis_id = serializers.IntegerField(required=False, allow_null=True)
    metadata = serializers.DictField(required=False, allow_null=True)
    message = serializers.CharField(required=False, allow_null=True)
