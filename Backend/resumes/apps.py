# resumes/apps.py
from django.apps import AppConfig

class ResumesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'resumes'
    verbose_name = 'Resume Management'
    
    def ready(self):
        """Import signals when app is ready"""
        try:
            import resumes.signals  # type: ignore # noqa: F401
        except ImportError:
            pass