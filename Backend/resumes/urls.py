# resumes/urls.py
from django.urls import path
from . import views

app_name = 'resumes'

urlpatterns = [
    # Class-based views
    path('', views.ResumeListCreateView.as_view(), name='resume-list-create'),
    path('<uuid:resume_id>/', views.ResumeDetailView.as_view(), name='resume-detail'),
    path('<uuid:resume_id>/reparse/', views.ResumeReparseView.as_view(), name='resume-reparse'),
    path('analytics/', views.ResumeAnalyticsView.as_view(), name='resume-analytics'),
    path('upload/', views.ResumeUploadView.as_view(), name='resume-upload'),
    
    # Function-based views (alternative endpoints)
    # path('api/upload/', views.upload_resume, name='upload-resume-func'),
    # path('api/list/', views.list_resumes, name='list-resumes-func'),
    # path('api/<uuid:resume_id>/', views.get_resume_detail, name='resume-detail-func'),
    # path('api/<uuid:resume_id>/reparse/', views.reparse_resume, name='reparse-resume-func'),
    # path('api/analytics/', views.get_resume_analytics, name='resume-analytics-func'),
    # path('api/search/skills/', views.search_resumes_by_skills, name='search-by-skills'),
    # path('api/<uuid:resume_id>/delete/', views.delete_resume, name='delete-resume'),
]

# Main project urls.py should include:
# path('resumes/', include('resumes.urls')),