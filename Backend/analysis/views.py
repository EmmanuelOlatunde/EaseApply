from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.db import transaction
import logging
from django.conf import settings

from jobs.models import JobDescription
from resumes.models import Resume
from .models import AnalysisResult
from .serializers import CoverLetterGenerateSerializer, CoverLetterResponseSerializer
from .services import OpenRouterService


logger = logging.getLogger(__name__)

class GenerateCoverLetterView(APIView):
    """
    Generate personalized cover letter using DeepSeek GPT API
    
    POST /analysis/generate-cover-letter/
    """
    permission_classes = [IsAuthenticated]
        
    def post(self, request):
        """Generate cover letter from job description and resume"""
        
        # Validate input data (but allow missing job_id/resume_id)
        serializer = CoverLetterGenerateSerializer(
            data=request.data, 
            context={'request': request},
            partial=True  # allow missing fields
        )
        
        if not serializer.is_valid():
            return Response({
                'success': False,
                'errors': serializer.errors,
                'message': 'Invalid input data'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        validated_data = serializer.validated_data
        
        # Get job_id & resume_id if provided
        job_id = validated_data.get('job_id')
        resume_id = validated_data.get('resume_id')
        
        try:
            # If no job_id provided → use latest job for the user
            if job_id is None:
                latest_job = JobDescription.objects.filter(user=request.user).order_by('-created_at').first()
                if not latest_job:
                    return Response({
                        'success': False,
                        'message': 'No job descriptions found for this user'
                    }, status=status.HTTP_404_NOT_FOUND)
                job_description = latest_job
            else:
                job_description = JobDescription.objects.get(id=job_id, user=request.user)
            
            # If no resume_id provided → use latest resume for the user
            if resume_id is None:
                latest_resume = Resume.objects.filter(user=request.user).order_by('-updated_at').first()
                if not latest_resume:
                    return Response({
                        'success': False,
                        'message': 'No resumes found for this user'
                    }, status=status.HTTP_404_NOT_FOUND)
                resume = latest_resume
            else:
                resume = Resume.objects.get(id=resume_id, user=request.user)
            
            

            ai_service = OpenRouterService()
            result = ai_service.generate_cover_letter(
                    title =job_description.title ,
                    company=job_description.company,
                    location=job_description.location,
                    job_type=job_description.job_type,
                    salary_range=job_description.salary_range,
                    requirements=job_description.requirements,
                    skills_required=job_description.skills_required,
                    experience_level=job_description.experience_level,
                    resume_content=resume.extracted_text,
                    template_type=request.data.get("template_type", "professional"),
                    #model=request.data.get("model", "")#qwen= , qw3n=
            )

            if not result['success']:
                return Response({
                    'success': False,
                    'message': result.get('error', 'Failed to generate cover letter'),
                    'error_type': result.get('error_type', 'unknown')
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
            # Save analysis result
            with transaction.atomic():
                analysis_result = AnalysisResult.objects.create(
                    user=request.user,
                    job_description=job_description,
                    resume=resume,
                    analysis_type='cover_letter',
                    prompt_used=result['prompt_used'],
                    result_text=result['cover_letter'],
                    model_used=result['metadata']['model'],
                    tokens_used=result['metadata']['tokens_used'],
                    processing_time=result['metadata']['processing_time']
                )
            
            response_data = {
                'success': True,
                'cover_letter': result['cover_letter'],
                'analysis_id': analysis_result.id,
                'metadata': {
                    'job_title': job_description.title,
                    'processing_time': result['metadata']['processing_time'],
                    'tokens_used': result['metadata']['tokens_used'],
                    'model_used': result['metadata']['model'],
                    'created_at': analysis_result.created_at.isoformat()
                },
                'message': 'Cover letter generated successfully'
            }
            
            # Validate response
            response_serializer = CoverLetterResponseSerializer(data=response_data)
            if response_serializer.is_valid():
                return Response(response_serializer.data, status=status.HTTP_201_CREATED)
            else:
                logger.error(f"Response serialization error: {response_serializer.errors}")
                return Response(response_data, status=status.HTTP_201_CREATED)
        
        except JobDescription.DoesNotExist:
            return Response({
                'success': False,
                'message': 'Job description not found or access denied'
            }, status=status.HTTP_404_NOT_FOUND)
        
        except Resume.DoesNotExist:
            return Response({
                'success': False,
                'message': 'Resume not found or access denied'
            }, status=status.HTTP_404_NOT_FOUND)
        
        except Exception as e:
            logger.error(f"Unexpected error in cover letter generation: {e}")
            return Response({
                'success': False,
                'message': 'Internal server error occurred',
                'error_details': str(e) if settings.DEBUG else None
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
