import logging
from rest_framework import generics, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser
from django.shortcuts import get_object_or_404
from django.db.models import Q
from .models import Resume
from .serializers import (
    ResumeUploadSerializer, 
    ResumeListSerializer, 
    ResumeDetailSerializer,
    ResumeParseSerializer,
    ResumeAnalyticsSerializer
)

logger = logging.getLogger(__name__)

class ResumeListCreateView(generics.ListCreateAPIView):
    """
    GET /resumes/ - List authenticated user's resumes
    POST /resumes/ - Upload and create new resume
    """
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def get_queryset(self):
        queryset = Resume.objects.filter(user=self.request.user).order_by('-uploaded_at')
        parsed_only = self.request.query_params.get('parsed')
        if parsed_only is not None:
            is_parsed = parsed_only.lower() in ['true', '1']
            queryset = queryset.filter(is_parsed=is_parsed)

        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                Q(full_name__icontains=search) |
                Q(original_filename__icontains=search)
            )
        return queryset

    def get_serializer_class(self):
        return ResumeUploadSerializer if self.request.method == 'POST' else ResumeListSerializer

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
        logger.info(f"Resume uploaded by user {self.request.user.id}")

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data, context={'request': request})
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        try:
            self.perform_create(serializer)
            headers = self.get_success_headers(serializer.data)
            detail_serializer = ResumeDetailSerializer(serializer.instance, context={'request': request})
            return Response(detail_serializer.data, status=status.HTTP_201_CREATED, headers=headers)
        except Exception as e:
            logger.error(f"Resume upload failed for user {request.user.id}: {str(e)}")
            return Response({'success': False, 'error': 'Failed to upload resume. Please try again.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ResumeDetailView(generics.RetrieveAPIView):
    """
    GET /resumes/<uuid>/ - Get resume details including extracted text and parsed data
    """
    serializer_class = ResumeDetailSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = 'id'
    lookup_url_kwarg = 'resume_id'

    def get_queryset(self):
        return Resume.objects.filter(user=self.request.user)


class ResumeReparseView(generics.UpdateAPIView):
    """
    PUT /resumes/<uuid>/reparse/ - Re-parse the extracted text
    """
    serializer_class = ResumeParseSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = 'id'
    lookup_url_kwarg = 'resume_id'

    def get_queryset(self):
        return Resume.objects.filter(user=self.request.user)

    def update(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            serializer = self.get_serializer(instance, data={}, partial=True)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"Resume re-parsing failed for {kwargs.get('resume_id')}: {str(e)}")
            return Response({'success': False, 'error': 'Failed to re-parse resume.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ResumeAnalyticsView(generics.ListAPIView):
    """
    GET /resumes/analytics/ - Get analytics for user's resumes
    """
    serializer_class = ResumeAnalyticsSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Resume.objects.filter(user=self.request.user).order_by('-uploaded_at')

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        total = queryset.count()
        parsed = queryset.filter(is_parsed=True).count()
        return Response({
            'summary': {
                'total_resumes': total,
                'parsed_resumes': parsed,
                'parsing_success_rate': round((parsed / total * 100), 1) if total > 0 else 0
            },
            'resumes': serializer.data
        })


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_resume(request, resume_id):
    try:
        resume = get_object_or_404(Resume, id=resume_id, user=request.user)
        filename = resume.original_filename
        resume.delete()
        logger.info(f"Resume {filename} deleted by user {request.user.id}")
        return Response({'success': True, 'message': 'Resume deleted successfully'}, status=status.HTTP_204_NO_CONTENT)
    except Exception as e:
        logger.error(f"Resume deletion failed for {resume_id}: {str(e)}")
        return Response({'success': False, 'error': 'Failed to delete resume.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def search_resumes_by_skills(request):
    skill = request.query_params.get('skill', '').strip()
    if not skill:
        return Response({'success': False, 'error': 'Skill parameter is required'}, status=status.HTTP_400_BAD_REQUEST)

    resumes = Resume.objects.filter(user=request.user, is_parsed=True, skills__icontains=skill).order_by('-uploaded_at')
    serializer = ResumeListSerializer(resumes, many=True, context={'request': request})
    return Response({
        'skill': skill,
        'count': resumes.count(),
        'resumes': serializer.data
    })
