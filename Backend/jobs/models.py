from django.db import models
from django.conf import settings
from django.utils import timezone
import os


def job_document_upload_path(instance, filename):
    """Generate upload path for job description documents"""
    return f'job_documents/{instance.user.id}/{filename}'


class JobDescription(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='job_descriptions'
    )
    
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
        if self.title and self.company:
            return f"{self.title} at {self.company}"
        return f"Job #{self.id}"

    def save(self, *args, **kwargs):
        self.updated_at = timezone.now()
        super().save(*args, **kwargs)
    
    def delete(self, *args, **kwargs):
        # Delete associated document file when job is deleted
        if self.document:
            if os.path.isfile(self.document.path):
                os.remove(self.document.path)
        super().delete(*args, **kwargs)