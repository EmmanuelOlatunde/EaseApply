
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from .models import JobDescription
from .serializers import (
    JobDescriptionSerializer,
    JobDescriptionUploadSerializer,
    JobDescriptionListSerializer
)
from .utils import extract_job_details


class JobDescriptionListCreateView(generics.ListCreateAPIView):
    """
    List all job descriptions for authenticated user or create a new one
    """
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return JobDescriptionUploadSerializer
        return JobDescriptionListSerializer

    def get_queryset(self):
        return JobDescription.objects.filter(user=self.request.user)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        job_description = serializer.save()
        response_serializer = JobDescriptionSerializer(job_description)
        headers = self.get_success_headers(serializer.data)
        return Response(
            {
                'message': 'Job description uploaded and processed successfully',
                'job_description': response_serializer.data,
                'extraction_status': {
                    'processed': job_description.is_processed,
                    'notes': job_description.processing_notes
                }
            },
            status=status.HTTP_201_CREATED,
            headers=headers
        )


class JobDescriptionDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve, update or delete a job description
    """
    serializer_class = JobDescriptionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return JobDescription.objects.filter(user=self.request.user)


class PasteJobDescriptionView(generics.CreateAPIView):
    """
    Paste job description text directly
    """
    serializer_class = JobDescriptionUploadSerializer
    permission_classes = [permissions.IsAuthenticated]

    def create(self, request, *args, **kwargs):
        raw_content = request.data.get('content', '').strip()

        if not raw_content:
            return Response(
                {'message': 'Job description content is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = self.get_serializer(data={'raw_content': raw_content}, context={'request': request})
        serializer.is_valid(raise_exception=True)
        job_description = serializer.save()
        response_serializer = JobDescriptionSerializer(job_description)

        return Response(
            {
                'message': 'Job description pasted and processed successfully',
                'job_description': response_serializer.data,
                'extraction_status': {
                    'processed': job_description.is_processed,
                    'notes': job_description.processing_notes
                }
            },
            status=status.HTTP_201_CREATED
        )


class UserJobListView(generics.ListAPIView):
    """
    Get all job descriptions for the authenticated user
    """
    serializer_class = JobDescriptionListSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return JobDescription.objects.filter(user=self.request.user)

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response({
            'count': queryset.count(),
            'processed_count': queryset.filter(is_processed=True).count(),
            'job_descriptions': serializer.data
        })


class JobReprocessView(generics.UpdateAPIView):
    """
    Reprocess a job description to extract details again
    """
    serializer_class = JobDescriptionSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_url_kwarg = 'job_id'

    def get_queryset(self):
        return JobDescription.objects.filter(user=self.request.user)

    def update(self, request, *args, **kwargs):
        job = self.get_object()

        if not job.raw_content:
            return Response(
                {'message': 'No raw content available for reprocessing'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            extracted_details = extract_job_details(job.raw_content)

            for field, value in extracted_details.items():
                if value:
                    setattr(job, field, value)

            job.is_processed = True
            job.processing_notes = "Successfully reprocessed and extracted job details"
            job.save()

            serializer = self.get_serializer(job)
            return Response(
                {
                    'message': 'Job description reprocessed successfully',
                    'job_description': serializer.data
                }
            )

        except Exception as e:
            job.is_processed = False
            job.processing_notes = f"Error during reprocessing: {str(e)}"
            job.save()

            return Response(
                {
                    'message': 'Error reprocessing job description',
                    'error': str(e)
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class JobDeleteView(generics.DestroyAPIView):
    """
    Delete a job description
    """
    serializer_class = JobDescriptionSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_url_kwarg = 'job_id'

    def get_queryset(self):
        return JobDescription.objects.filter(user=self.request.user)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response(
            {'message': 'Job description deleted successfully'},
            status=status.HTTP_204_NO_CONTENT
        )
