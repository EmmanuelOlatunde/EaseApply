# resumes/views.py
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
    API endpoint for listing user's resumes and creating new ones
    
    GET /resumes/ - List authenticated user's resumes
    POST /resumes/ - Upload and create new resume  # Updated endpoint
    """
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]
    
    def get_queryset(self):
        """Return only the authenticated user's resumes with optional filtering"""
        queryset = Resume.objects.filter(user=self.request.user).order_by('-uploaded_at')
        
        # Filter by parsing status
        parsed_only = self.request.query_params.get('parsed', None)
        if parsed_only is not None:
            is_parsed = parsed_only.lower() in ['true', '1']
            queryset = queryset.filter(is_parsed=is_parsed)
        
        # Search by name or filename
        search = self.request.query_params.get('search', None)
        if search:
            queryset = queryset.filter(
                Q(full_name__icontains=search) | 
                Q(original_filename__icontains=search)
            )
        
        return queryset
    
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
            # Return detailed serializer data instead of upload serializer
            instance = serializer.instance
            detail_serializer = ResumeDetailSerializer(instance, context={'request': request})
            return Response(detail_serializer.data, status=status.HTTP_201_CREATED, headers=headers)
        except Exception as e:
            logger.error(f"Resume upload failed for user {request.user.id}: {str(e)}")
            return Response(
                {'error': 'Failed to upload resume. Please try again.'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class ResumeDetailView(generics.RetrieveAPIView):
    """
    API endpoint for retrieving a single resume with all parsed data
    
    GET /resumes/<uuid>/ - Get resume details including extracted text and parsed data
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

class ResumeReparseView(generics.UpdateAPIView):
    """
    API endpoint for re-parsing an existing resume
    
    PUT /resumes/<uuid>/reparse/ - Re-parse the extracted text
    """
    serializer_class = ResumeParseSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = 'id'
    lookup_url_kwarg = 'resume_id'
    
    def get_queryset(self):
        """Return only the authenticated user's resumes"""
        return Resume.objects.filter(user=self.request.user)
    
    def update(self, request, *args, **kwargs):
        """Handle the re-parsing request"""
        try:
            instance = self.get_object()
            serializer = self.get_serializer(instance, data={}, partial=True)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"Resume re-parsing failed for {kwargs.get('resume_id')}: {str(e)}")
            return Response(
                {'error': 'Failed to re-parse resume.'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class ResumeAnalyticsView(generics.ListAPIView):
    """
    API endpoint for resume analytics and statistics
    
    GET /resumes/analytics/ - Get analytics for user's resumes
    """
    serializer_class = ResumeAnalyticsSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Return only the authenticated user's resumes"""
        return Resume.objects.filter(user=self.request.user).order_by('-uploaded_at')

# Function-based views (alternatives to class-based views)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def upload_resume(request):
    """
    Function-based view for resume upload with parsing
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
    Function-based view for listing user's resumes with filtering
    """
    queryset = Resume.objects.filter(user=request.user).order_by('-uploaded_at')
    
    # Apply filters
    parsed_only = request.query_params.get('parsed', None)
    if parsed_only is not None:
        is_parsed = parsed_only.lower() in ['true', '1']
        queryset = queryset.filter(is_parsed=is_parsed)
    
    search = request.query_params.get('search', None)
    if search:
        queryset = queryset.filter(
            Q(full_name__icontains=search) | 
            Q(original_filename__icontains=search)
        )
    
    serializer = ResumeListSerializer(queryset, many=True, context={'request': request})
    return Response(serializer.data)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_resume_detail(request, resume_id):
    """
    Function-based view for getting resume details with all parsed data
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

@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def reparse_resume(request, resume_id):
    """
    Function-based view for re-parsing a resume
    """
    try:
        resume = get_object_or_404(Resume, id=resume_id, user=request.user)
        serializer = ResumeParseSerializer(resume, data={}, partial=True)
        
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
    except Exception as e:
        logger.error(f"Resume re-parsing failed for {resume_id}: {str(e)}")
        return Response(
            {'error': 'Failed to re-parse resume.'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_resume_analytics(request):
    """
    Function-based view for resume analytics
    """
    resumes = Resume.objects.filter(user=request.user).order_by('-uploaded_at')
    serializer = ResumeAnalyticsSerializer(resumes, many=True, context={'request': request})
    
    # Calculate summary statistics
    total_resumes = resumes.count()
    parsed_resumes = resumes.filter(is_parsed=True).count()
    
    response_data = {
        'summary': {
            'total_resumes': total_resumes,
            'parsed_resumes': parsed_resumes,
            'parsing_success_rate': round((parsed_resumes / total_resumes * 100), 1) if total_resumes > 0 else 0
        },
        'resumes': serializer.data
    }
    
    return Response(response_data)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def search_resumes_by_skills(request):
    """
    Search resumes by skills
    """
    skill = request.query_params.get('skill', '').strip()
    if not skill:
        return Response({'error': 'Skill parameter is required'}, status=status.HTTP_400_BAD_REQUEST)
    
    # Search for resumes containing the skill (case-insensitive)
    resumes = Resume.objects.filter(
        user=request.user,
        is_parsed=True,
        skills__icontains=skill
    ).order_by('-uploaded_at')
    
    serializer = ResumeListSerializer(resumes, many=True, context={'request': request})
    
    return Response({
        'skill': skill,
        'count': resumes.count(),
        'resumes': serializer.data
    })

@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_resume(request, resume_id):
    """
    Delete a resume
    """
    try:
        resume = get_object_or_404(Resume, id=resume_id, user=request.user)
        filename = resume.original_filename
        resume.delete()
        
        logger.info(f"Resume {filename} deleted by user {request.user.id}")
        return Response({'message': 'Resume deleted successfully'}, status=status.HTTP_204_NO_CONTENT)
        
    except Exception as e:
        logger.error(f"Resume deletion failed for {resume_id}: {str(e)}")
        return Response(
            {'error': 'Failed to delete resume.'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )