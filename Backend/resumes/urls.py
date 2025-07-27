from django.urls import path, register_converter
from uuid import UUID
from . import views

class CaseInsensitiveUUIDConverter:
    regex = '[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}'

    def to_python(self, value):
        return UUID(value.lower())

    def to_url(self, value):
        return str(value)

register_converter(CaseInsensitiveUUIDConverter, 'uuid')

app_name = 'resumes'

urlpatterns = [
    # Class-based views (recommended)
    path('', views.ResumeListCreateView.as_view(), name='resume-list-create'),
    path('upload/', views.ResumeListCreateView.as_view(), name='resume-upload'),
    path('<uuid:resume_id>/', views.ResumeDetailView.as_view(), name='resume-detail'),
    
    # Alternative function-based views (uncomment if preferred)
    # path('upload/', views.upload_resume, name='resume-upload'),
    # path('list/', views.list_resumes, name='resume-list'),
    # path('<uuid:resume_id>/', views.get_resume_detail, name='resume-detail'),
]

