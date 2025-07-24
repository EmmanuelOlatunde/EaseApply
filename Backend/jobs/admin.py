from django.contrib import admin
from .models import JobDescription


@admin.register(JobDescription)
class JobDescriptionAdmin(admin.ModelAdmin):
    list_display = [
        'id',
        'title',
        'company',
        'user',
        'job_type',
        'location',
        'is_processed',
        'created_at',
        'is_active'
    ]
    list_filter = [
        'job_type',
        'is_processed',
        'is_active',
        'created_at',
        'experience_level'
    ]
    search_fields = [
        'title',
        'company',
        'location',
        'user__username',
        'user__email'
    ]
    readonly_fields = [
        'created_at',
        'updated_at',
        'is_processed',
        'processing_notes'
    ]
    fieldsets = (
        ('Basic Information', {
            'fields': ('user', 'is_active', 'created_at', 'updated_at')
        }),
        ('Raw Content', {
            'fields': ('raw_content', 'document'),
            'classes': ('collapse',)
        }),
        ('Extracted Details', {
            'fields': (
                'title',
                'company',
                'location',
                'job_type',
                'salary_range',
                'experience_level'
            )
        }),
        ('Requirements & Skills', {
            'fields': ('requirements', 'skills_required'),
            'classes': ('collapse',)
        }),
        ('Processing Status', {
            'fields': ('is_processed', 'processing_notes'),
            'classes': ('collapse',)
        })
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user')