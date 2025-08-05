
from django.urls import path
from .views import GenerateCoverLetterView

app_name = 'analysis'

urlpatterns = [
    path('generate-cover-letter/', GenerateCoverLetterView.as_view(), name='generate-cover-letter'),
]