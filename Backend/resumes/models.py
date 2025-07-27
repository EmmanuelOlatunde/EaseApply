import uuid
import os
from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import FileExtensionValidator

User = get_user_model()

def resume_upload_path(instance, filename):
    """Generate upload path for resume files"""
    ext = filename.split('.')[-1]
    filename = f"{uuid.uuid4()}.{ext}"
    return os.path.join('resumes', str(instance.user.id), filename)

class Resume(models.Model):
    DOCX = 'docx'
    PDF = 'pdf'
    
    FILE_TYPE_CHOICES = [
        (DOCX, 'DOCX'),
        (PDF, 'PDF'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='resumes'
    )
    file = models.FileField(
        upload_to=resume_upload_path,
        validators=[FileExtensionValidator(allowed_extensions=['pdf', 'docx'])]
    )
    original_filename = models.CharField(max_length=255)
    file_type = models.CharField(
        max_length=10, 
        choices=FILE_TYPE_CHOICES
    )
    extracted_text = models.TextField(blank=True, null=True)
    file_size = models.PositiveIntegerField(help_text="File size in bytes")
    
    # Timestamps
    uploaded_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-uploaded_at']
        indexes = [
            models.Index(fields=['user', '-uploaded_at']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.original_filename}"
    
    def save(self, *args, **kwargs):
        if self.file:
            # Set original filename if not already set
            if not self.original_filename:
                self.original_filename = self.file.name
            
            # Detect file type from extension
            if not self.file_type:
                ext = self.original_filename.lower().split('.')[-1]
                if ext == 'pdf':
                    self.file_type = self.PDF
                elif ext in ['docx', 'doc']:
                    self.file_type = self.DOCX
            
            # Set file size
            if not self.file_size and hasattr(self.file, 'size'):
                self.file_size = self.file.size
        
        super().save(*args, **kwargs)