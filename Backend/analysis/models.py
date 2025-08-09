from django.db import models
from django.contrib.auth import get_user_model
from jobs.models import JobDescription
from resumes.models import Resume

User = get_user_model()

class AnalysisResult(models.Model):
    """Store analysis results including cover letters"""
    
    ANALYSIS_TYPES = [
        ('cover_letter', 'Cover Letter'),
        ('resume_analysis', 'Resume Analysis'),
        ('job_match', 'Job Match Score'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='analysis_results')
    job_description = models.ForeignKey(JobDescription, on_delete=models.CASCADE, null=True, blank=True)
    resume = models.ForeignKey(Resume, on_delete=models.CASCADE, null=True, blank=True)
    
    analysis_type = models.CharField(max_length=20, choices=ANALYSIS_TYPES, default='cover_letter')
    prompt_used = models.TextField(help_text="The prompt sent to AI model")
    result_text = models.TextField(help_text="Generated content from AI")
    
    # Metadata
    model_used = models.CharField(max_length=100, default='gpt-4o')
    tokens_used = models.IntegerField(null=True, blank=True)
    processing_time = models.FloatField(null=True, blank=True, help_text="Time in seconds")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'analysis_type']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.analysis_type} - {self.created_at.strftime('%Y-%m-%d')}"
