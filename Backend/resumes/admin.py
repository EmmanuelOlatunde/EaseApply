# resumes/admin.py
from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from .models import Resume

@admin.register(Resume)
class ResumeAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'user_link', 'original_filename', 'file_type', 
        'file_size_mb', 'has_extracted_text', 'uploaded_at'
    ]
    list_filter = ['file_type', 'uploaded_at', 'user']
    search_fields = ['original_filename', 'user__username', 'user__email']
    readonly_fields = [
        'id', 'file_size', 'uploaded_at', 'updated_at', 
        'extracted_text_preview'
    ]
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('id', 'user', 'original_filename', 'file_type')
        }),
        ('File Details', {
            'fields': ('file', 'file_size', 'uploaded_at', 'updated_at')
        }),
        ('Extracted Content', {
            'fields': ('extracted_text_preview',),
            'classes': ('collapse',)
        }),
    )
    
    def user_link(self, obj):
        """Create a link to the user's admin page"""
        url = reverse('admin:auth_user_change', args=[obj.user.pk])
        return format_html('<a href="{}">{}</a>', url, obj.user.username)
    user_link.short_description = 'User'
    
    def file_size_mb(self, obj):
        """Display file size in MB"""
        if obj.file_size:
            return f"{obj.file_size / (1024 * 1024):.2f} MB"
        return "N/A"
    file_size_mb.short_description = 'File Size'
    
    def has_extracted_text(self, obj):
        """Show if text was extracted successfully"""
        if obj.extracted_text:
            if "extraction failed" in obj.extracted_text.lower():
                return format_html('<span style="color: red;">❌ Failed</span>')
            return format_html('<span style="color: green;">✅ Success</span>')
        return format_html('<span style="color: orange;">⚠️ No Text</span>')
    has_extracted_text.short_description = 'Text Extraction'
    
    def extracted_text_preview(self, obj):
        """Show a preview of extracted text"""
        if obj.extracted_text:
            preview = obj.extracted_text[:500]
            if len(obj.extracted_text) > 500:
                preview += "..."
            return format_html('<pre style="white-space: pre-wrap;">{}</pre>', preview)
        return "No extracted text available"
    extracted_text_preview.short_description = 'Extracted Text Preview'

# ============================================
# requirements.txt additions
# ============================================

"""
Add these packages to your requirements.txt:

PyPDF2==3.0.1
python-docx==0.8.11
djangorestframework==3.14.0
Pillow==10.0.0  # For ImageField support if needed

# Or install via pip:
pip install PyPDF2==3.0.1 python-docx==0.8.11 djangorestframework==3.14.0 Pillow==10.0.0
"""

# ============================================
# Migration commands
# ============================================

"""
After setting up the app, run these Django commands:

1. Create and apply migrations:
   python manage.py makemigrations resumes
   python manage.py migrate

2. Create superuser (if not already done):
   python manage.py createsuperuser

3. Collect static files (for production):
   python manage.py collectstatic
"""