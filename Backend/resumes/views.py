# resumes/views.py
import logging
from rest_framework.views import APIView
from rest_framework import generics, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser
from django.shortcuts import get_object_or_404
from .models import Resume
from .serializers import (
    ResumeUploadSerializer, 
    ResumeListSerializer, 
    ResumeDetailSerializer
)

logger = logging.getLogger(__name__)

class ResumeListCreateView(generics.ListCreateAPIView):
    """
    API endpoint for listing user's resumes and creating new ones
    
    GET /resumes/ - List authenticated user's resumes
    POST /resumes/upload/ - Upload and create new resume with text extraction
    """
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]
    
    def get_queryset(self):
        """Return only the authenticated user's resumes"""
        return Resume.objects.filter(user=self.request.user).order_by('-uploaded_at')
    
    def get_serializer_class(self):
        """Return appropriate serializer based on request method"""
        if self.request.method == 'POST':
            return ResumeUploadSerializer
        return ResumeListSerializer
    
    def perform_create(self, serializer):
        """Save the resume with the authenticated user"""
        serializer.save(user=self.request.user)
        logger.info(f"Resume uploaded by user {self.request.user.id}")
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data, context={'request': request})
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        try:
            self.perform_create(serializer)
            headers = self.get_success_headers(serializer.data)
            return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
        except Exception as e:
            logger.error(f"Resume upload failed for user {request.user.id}: {str(e)}")
            return Response(
                {'error': 'Failed to upload resume. Please try again.'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class ResumeDetailView(generics.RetrieveAPIView):
    """
    API endpoint for retrieving a single resume with extracted text
    
    GET /resumes/<uuid>/ - Get resume details including extracted text
    """
    serializer_class = ResumeDetailSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = 'id'
    lookup_url_kwarg = 'resume_id'
    
    def get_queryset(self):
        """Return only the authenticated user's resumes"""
        return Resume.objects.filter(user=self.request.user)
    
    def get_object(self):
        """Get resume object with proper error handling"""
        queryset = self.get_queryset()
        resume_id = self.kwargs.get('resume_id')
        
        try:
            obj = get_object_or_404(queryset, id=resume_id)
            return obj
        except Exception as e:  # noqa: F841
            logger.error(f"Resume {resume_id} not found for user {self.request.user.id}")
            raise

class ResumeUploadView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request, *args, **kwargs):
        try:
            serializer = ResumeUploadSerializer(
                data=request.data,
                context={'request': request}
            )
            if not serializer.is_valid():
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            resume = serializer.save(user=request.user)
            return Response(
                ResumeDetailSerializer(resume, context={'request': request}).data,
                status=status.HTTP_201_CREATED
            )
        except Exception as e:
            logger.error(f"Resume upload failed for user {request.user.id}: {str(e)}")
            return Response(
                {'error': 'Invalid request format. Please use multipart/form-data.'},
                status=status.HTTP_400_BAD_REQUEST
            )

# Alternative function-based view for upload endpoint
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def upload_resume(request):
    """
    Function-based view for resume upload
    Alternative to the class-based view above
    """
    if request.method == 'POST':
        serializer = ResumeUploadSerializer(
            data=request.data, 
            context={'request': request}
        )
        
        if serializer.is_valid():
            try:
                resume = serializer.save()
                response_serializer = ResumeDetailSerializer(
                    resume, 
                    context={'request': request}
                )
                logger.info(f"Resume successfully uploaded by user {request.user.id}")
                return Response(
                    response_serializer.data, 
                    status=status.HTTP_201_CREATED
                )
            except Exception as e:
                logger.error(f"Resume upload failed for user {request.user.id}: {str(e)}")
                return Response(
                    {'error': 'Failed to process resume upload.'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_resumes(request):
    """
    Function-based view for listing user's resumes
    Alternative to the class-based view above
    """
    resumes = Resume.objects.filter(user=request.user).order_by('-uploaded_at')
    serializer = ResumeListSerializer(resumes, many=True, context={'request': request})
    return Response(serializer.data)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_resume_detail(request, resume_id):
    """
    Function-based view for getting resume details
    Alternative to the class-based view above
    """
    try:
        resume = get_object_or_404(Resume, id=resume_id, user=request.user)
        serializer = ResumeDetailSerializer(resume, context={'request': request})
        return Response(serializer.data)
    except Exception as e:  # noqa: F841
        logger.error(f"Resume {resume_id} not found for user {request.user.id}")
        return Response(
            {'error': 'Resume not found.'},
            status=status.HTTP_404_NOT_FOUND
        )