from django.contrib import admin
from django.utils.html import format_html
from .models import Resume

@admin.register(Resume)
class ResumeAdmin(admin.ModelAdmin):
    list_display = [
        'original_filename', 'user_email', 'full_name', 
        'file_type', 'file_size_display', 'is_parsed', 
        'skills_count', 'uploaded_at'
    ]
    list_filter = [
        'file_type', 'is_parsed', 'uploaded_at', 'parsed_at'
    ]
    search_fields = [
        'user__email', 'user__username', 'original_filename', 
        'full_name', 'contact_info__email'
    ]
    readonly_fields = [
        'id', 'uploaded_at', 'updated_at', 'parsed_at', 
        'file_size', 'file_url_display'
    ]
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('id', 'user', 'original_filename', 'file_type', 'file_size')
        }),
        ('File', {
            'fields': ('file', 'file_url_display')
        }),
        ('Parsed Data', {
            'fields': (
                'full_name', 'summary', 'contact_info', 'skills',
                'work_experience', 'education', 'certifications', 'projects'
            ),
            'classes': ('collapse',)
        }),
        ('Text Content', {
            'fields': ('extracted_text',),
            'classes': ('collapse',)
        }),
        ('Processing Status', {
            'fields': ('is_parsed', 'parsing_error', 'parsed_at')
        }),
        ('Timestamps', {
            'fields': ('uploaded_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def user_email(self, obj):
        return obj.user.email
    user_email.short_description = 'User Email'
    user_email.admin_order_field = 'user__email'
    
    def file_size_display(self, obj):
        if obj.file_size:
            if obj.file_size < 1024:
                return f"{obj.file_size} B"
            elif obj.file_size < 1024**2:
                return f"{obj.file_size/1024:.1f} KB"
            else:
                return f"{obj.file_size/(1024**2):.1f} MB"
        return "Unknown"
    file_size_display.short_description = 'File Size'
    
    def skills_count(self, obj):
        return len(obj.skills) if obj.skills else 0
    skills_count.short_description = 'Skills Count'
    
    def file_url_display(self, obj):
        if obj.file:
            return format_html(
                '<a href="{}" target="_blank">Download File</a>',
                obj.file.url
            )
        return "No file"
    file_url_display.short_description = 'File URL'
    
    actions = ['reparse_resumes', 'mark_as_unparsed']
    
    def reparse_resumes(self, request, queryset):
        """Admin action to reparse selected resumes"""
        from .utils import parse_resume_content, ResumeParsingError
        from django.utils import timezone
        
        success_count = 0
        error_count = 0
        
        for resume in queryset:
            if resume.extracted_text:
                try:
                    parsed_data = parse_resume_content(resume.extracted_text)
                    resume.full_name = parsed_data.get('fullName')
                    resume.summary = parsed_data.get('summary')
                    resume.contact_info = parsed_data.get('contactInfo', {})
                    resume.skills = parsed_data.get('skills', [])
                    resume.work_experience = parsed_data.get('workExperience', [])
                    resume.education = parsed_data.get('education', [])
                    resume.certifications = parsed_data.get('certifications', [])
                    resume.projects = parsed_data.get('projects', [])
                    resume.is_parsed = True
                    resume.parsing_error = None
                    resume.parsed_at = timezone.now()
                    resume.save()
                    success_count += 1
                except ResumeParsingError as e:
                    resume.parsing_error = str(e)
                    resume.is_parsed = False
                    resume.save()
                    error_count += 1
            else:
                error_count += 1
        
        self.message_user(
            request,
            f"Successfully reparsed {success_count} resumes. {error_count} failed."
        )
    reparse_resumes.short_description = "Reparse selected resumes"
    
    def mark_as_unparsed(self, request, queryset):
        """Mark selected resumes as unparsed"""
        updated = queryset.update(is_parsed=False, parsing_error="Manually marked as unparsed")
        self.message_user(request, f"Marked {updated} resumes as unparsed.")
    mark_as_unparsed.short_description = "Mark as unparsed"