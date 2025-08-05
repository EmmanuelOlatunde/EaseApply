from django.db import models
from django.conf import settings
from django.utils import timezone
import os
import uuid

def job_document_upload_path(instance, filename):
    """Generate upload path for job description documents"""
    return f'job_documents/{instance.user.id}/{filename}'


class JobDescription(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='job_descriptions'
        
    )
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    # Original content
    raw_content = models.TextField(help_text="Original job description content")
    document = models.FileField(
        upload_to=job_document_upload_path,
        blank=True,
        null=True,
        help_text="Optional: Upload job description document"
    )
    
    # Extracted fields (auto-populated from raw_content)
    title = models.CharField(max_length=200, blank=True)
    company = models.CharField(max_length=200, blank=True)
    location = models.CharField(max_length=200, blank=True, null=True)
    job_type = models.CharField(
        max_length=50,
        choices=[
            ('full_time', 'Full Time'),
            ('part_time', 'Part Time'),
            ('contract', 'Contract'),
            ('internship', 'Internship'),
            ('remote', 'Remote'),
            ('unknown', 'Unknown'),
        ],
        default='unknown'
    )
    salary_range = models.CharField(max_length=100, blank=True, null=True)
    requirements = models.TextField(blank=True, null=True)
    skills_required = models.TextField(blank=True, null=True)
    experience_level = models.CharField(max_length=100, blank=True, null=True)
    
    # Processing status
    is_processed = models.BooleanField(default=False)
    processing_notes = models.TextField(blank=True, null=True)
    
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Job Description'
        verbose_name_plural = 'Job Descriptions'

    def __str__(self):
        title = (self.title or '').strip()
        company = (self.company or '').strip()

        if title and company:
            return f"{title} at {company}"
        return f"Job #{self.id}"


    def save(self, *args, **kwargs):
        if self.title:
            self.title = self.title[:200]
        if self.company:
            self.company = self.company[:200]
        if self.location:
            self.location = self.location[:200]
        self.updated_at = timezone.now()
        super().save(*args, **kwargs)
    
    def delete(self, *args, **kwargs):
        if self.document:
            file_path = self.document.path
            if os.path.isfile(file_path):  # ✅ this triggers mock_isfile
                try:
                    os.remove(file_path)
                except (FileNotFoundError, OSError):
                    pass
        super().delete(*args, **kwargs)
