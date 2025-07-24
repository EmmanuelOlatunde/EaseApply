from django.urls import path
from . import views

app_name = 'jobs'

urlpatterns = [
    # Main CRUD endpoints
    path('', views.JobDescriptionListCreateView.as_view(), name='job-list-create'),
    path('<int:pk>/', views.JobDescriptionDetailView.as_view(), name='job-detail'),

    # Upload / Paste endpoints
    path('paste/', views.PasteJobDescriptionView.as_view(), name='paste-job'),

    # User job listing
    path('my-jobs/', views.UserJobListView.as_view(), name='user-jobs'),

    # Reprocess and delete
    path('reprocess/<int:job_id>/', views.JobReprocessView.as_view(), name='reprocess-job'),
    path('delete/<int:job_id>/', views.JobDeleteView.as_view(), name='delete-job'),
]