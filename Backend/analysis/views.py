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
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from common.redis_service import app_cache  # Import your caching layer



logger = logging.getLogger(__name__)


class GenerateCoverLetterView(APIView):
    """
    Generate personalized cover letter using DeepSeek GPT API
    
    POST /analysis/generate-cover-letter/
    """
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def post(self, request):
        serializer = CoverLetterGenerateSerializer(
            data=request.data, 
            context={'request': request},
            partial=True
        )

        if not serializer.is_valid():
            return Response({
                'success': False,
                'errors': serializer.errors,
                'message': 'Invalid input data'
            }, status=status.HTTP_400_BAD_REQUEST)

        validated_data = serializer.validated_data
        job_id = validated_data.get('job_id')
        resume_id = validated_data.get('resume_id')
        template_type = validated_data.get("template_type", "professional")

        try:
            job_description = JobDescription.objects.filter(user=request.user)
            resume = Resume.objects.filter(user=request.user)

            job_description = job_description.get(id=job_id) if job_id else job_description.order_by('-created_at').first()
            if not job_description:
                return Response({'success': False, 'message': 'No job descriptions found'}, status=status.HTTP_404_NOT_FOUND)

            resume = resume.get(id=resume_id) if resume_id else resume.order_by('-updated_at').first()
            if not resume:
                return Response({'success': False, 'message': 'No resumes found'}, status=status.HTTP_404_NOT_FOUND)

            if not resume.extracted_text or not resume.extracted_text.strip():
                return Response({
                    "success": False,
                    "errors": {"resume_id": ["Resume must have valid extracted text."]},
                    "message": "Invalid input data"
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # ----------------- CACHING CHECK -----------------
            cache_key = f"cover_letter:{request.user.id}:{job_description.id}:{resume.id}:{template_type}"
            cached_data = app_cache.redis.get(cache_key)
            if cached_data:
                logger.info(f"✅ Returning cached cover letter for key {cache_key}")
                return Response(cached_data, status=status.HTTP_200_OK)
            # --------------------------------------------------

            import asyncio
            ai_service = OpenRouterService()
            try:
                result = asyncio.run(
                    ai_service.generate_cover_letter(
                        title=job_description.title,
                        company=job_description.company,
                        location=job_description.location,
                        job_type=job_description.job_type,
                        salary_range=job_description.salary_range,
                        requirements=job_description.requirements,
                        skills_required=job_description.skills_required,
                        experience_level=job_description.experience_level,
                        resume_content=resume.extracted_text,
                        template_type=template_type,
                    )
                )
            except Exception as ai_error:
                logger.error(f"AI service error: {ai_error}")
                return Response({
                    'success': False,
                    'message': 'AI service encountered an error',
                    'error_type': 'ai_service_error'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            if not result['success']:
                return Response({
                    'success': False,
                    'message': result.get('error', 'Failed to generate cover letter'),
                    'error_type': result.get('error_type', 'unknown')
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            try:
                with transaction.atomic():
                    job_description = JobDescription.objects.get(pk=job_description.id)
                    resume = Resume.objects.get(pk=resume.id)

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
            except (JobDescription.DoesNotExist, Resume.DoesNotExist):
                logger.warning("Race condition: job or resume was deleted during generation.")
                return Response({
                    "success": False,
                    "message": "The job or resume was deleted before the analysis could be saved."
                }, status=status.HTTP_410_GONE)
            except Exception as db_error:
                logger.error(f"Database error during analysis result creation: {db_error}")
                return Response({
                    'success': False,
                    'message': 'Database error occurred while saving analysis result',
                    'error_type': 'database_error'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

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

            # ----------------- SAVE TO CACHE -----------------
            app_cache.redis.set(
                cache_key,
                response_data,
                timeout=60 * 60 * 6  # Cache for 6 hours
            )
            # --------------------------------------------------

            response_serializer = CoverLetterResponseSerializer(data=response_data)
            if response_serializer.is_valid():
                return Response(response_serializer.data, status=status.HTTP_201_CREATED)
            else:
                logger.error(f"Response serialization error: {response_serializer.errors}")
                return Response(response_data, status=status.HTTP_201_CREATED)

        except Exception as e:
            logger.error(f"Unexpected error in cover letter generation: {e}")
            return Response({
                'success': False,
                'message': 'Internal server error occurred',
                'error_details': str(e) if settings.DEBUG else None
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
