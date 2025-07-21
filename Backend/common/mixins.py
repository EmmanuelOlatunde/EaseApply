from rest_framework.response import Response
from rest_framework import status
from django.core.exceptions import ValidationError
from django.db import IntegrityError
import logging

logger = logging.getLogger(__name__)


class StandardResponseMixin:
    """Mixin to provide standardized API responses"""
    
    def success_response(self, data=None, message="Success", status_code=status.HTTP_200_OK):
        """Return standardized success response"""
        response_data = {
            'success': True,
            'message': message,
        }
        if data is not None:
            response_data['data'] = data
        return Response(response_data, status=status_code)
    
    def error_response(self, message="Error occurred", errors=None, status_code=status.HTTP_400_BAD_REQUEST):
        """Return standardized error response"""
        response_data = {
            'success': False,
            'message': message,
        }
        if errors:
            response_data['errors'] = errors
        return Response(response_data, status=status_code)


class ExceptionHandlerMixin:
    """Mixin to handle common exceptions in views"""
    
    def handle_exception(self, exc):
        """Handle common exceptions and return appropriate responses"""
        if isinstance(exc, ValidationError):
            return self.error_response(
                message="Validation error",
                errors=exc.message_dict if hasattr(exc, 'message_dict') else str(exc),
                status_code=status.HTTP_400_BAD_REQUEST
            )
        elif isinstance(exc, IntegrityError):
            logger.error(f"IntegrityError: {str(exc)}")
            return self.error_response(
                message="Data integrity error",
                status_code=status.HTTP_409_CONFLICT
            )
        return super().handle_exception(exc)


class LoggingMixin:
    """Mixin to add logging to views"""
    
    def dispatch(self, request, *args, **kwargs):
        """Log request details"""
        logger.info(f"{request.method} {request.path} - User: {getattr(request.user, 'email', 'Anonymous')}")
        response = super().dispatch(request, *args, **kwargs)
        logger.info(f"Response status: {response.status_code}")
        return response


class PaginationMixin:
    """Mixin to add consistent pagination"""
    
    def get_paginated_response_data(self, paginated_queryset):
        """Return paginated response data"""
        return {
            'count': paginated_queryset.paginator.count,
            'next': paginated_queryset.next_page_number() if paginated_queryset.has_next() else None,
            'previous': paginated_queryset.previous_page_number() if paginated_queryset.has_previous() else None,
            'results': paginated_queryset.object_list
        }