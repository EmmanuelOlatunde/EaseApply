from django.contrib import admin
from .models import AnalysisResult


@admin.register(AnalysisResult)
class AnalysisResultAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'analysis_type', 'model_used', 'created_at']
    list_filter = ['analysis_type', 'model_used', 'created_at']
    search_fields = ['user__username', 'result_text']
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['-created_at']