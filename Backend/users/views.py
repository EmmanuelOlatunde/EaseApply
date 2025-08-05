from rest_framework import status, generics, permissions
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from rest_framework.views import APIView
from django.contrib.auth.models import update_last_login
from .models import User
from .serializers import (
    UserRegistrationSerializer, 
    UserLoginSerializer, 
    UserProfileSerializer,
    ChangePasswordSerializer,
    PasswordResetRequestSerializer,
    ResetPasswordConfirmSerializer
)
from common.permissions import IsOwnerOrReadOnly
from common.utils import get_client_ip, send_verification_email
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.throttling import AnonRateThrottle

from rest_framework.permissions import AllowAny
from django.utils.http import urlsafe_base64_decode
from django.utils.encoding import force_str
from django.contrib.auth.tokens import default_token_generator
from common.utils import send_password_reset_email


class RegisterView(generics.CreateAPIView):
    """User registration endpoint"""
    queryset = User.objects.all()
    serializer_class = UserRegistrationSerializer
    permission_classes = [permissions.AllowAny]
    
    def perform_create(self, serializer):
        user = serializer.save()
        try:
            send_verification_email(user)
        except Exception as e:
            # Log the failure but don't block registration
            print(f"Email sending failed: {e}")
        return user

class LoginView(APIView):
    """User login endpoint with JWT"""
    permission_classes = [permissions.AllowAny]

    @swagger_auto_schema(
        operation_description="Login with email and password to get JWT access & refresh tokens",
        request_body=UserLoginSerializer,
        responses={
            200: openapi.Response(
                description="Login successful",
                examples={
                    "application/json": {
                        "access": "jwt_access_token_here",
                        "refresh": "jwt_refresh_token_here",
                        "user": {
                            "id": 1,
                            "email": "test@example.com",
                            "username": "testuser"
                        }
                    }
                }
            ),
            400: "Invalid credentials"
        }
    )
    def post(self, request):
        serializer = UserLoginSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data['user']

            # ✅ Generate JWT tokens
            refresh = RefreshToken.for_user(user)

            # ✅ Update last login info
            update_last_login(None, user)
            user.last_login_ip = get_client_ip(request)
            user.save(update_fields=['last_login_ip'])

            return Response({
                "access": str(refresh.access_token),  # short-lived token
                "refresh": str(refresh),              # long-lived token
                "user": UserProfileSerializer(user).data
            }, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class LogoutView(APIView):
    """User logout endpoint"""
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        try:
            request.user.auth_token.delete()
        except:  # noqa: E722
            pass
        return Response({'message': 'Successfully logged out'})
    
class ProfileView(generics.RetrieveUpdateAPIView):
    """User profile retrieve and update endpoint"""
    serializer_class = UserProfileSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrReadOnly]
    
    def get_object(self):
        return self.request.user

class ChangePasswordView(APIView):
    """Change password endpoint"""
    permission_classes = [permissions.IsAuthenticated]
    @swagger_auto_schema(
        operation_description="Password Change",
        request_body=ChangePasswordSerializer,
        responses={
            200: openapi.Response(
                description="Password successful Changed",
                examples={
                    "application/json": {
                        "access": "jwt_access_token_here",
                        "refresh": "jwt_refresh_token_here",
                        "user": {
                            "id": 1,
                            "email": "test@example.com",
                            "username": "testuser"
                        }
                    }
                }
            ),
            400: "Invalid credentials"
        }
    )
    def put(self, request):
        serializer = ChangePasswordSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            user = request.user
            user.set_password(serializer.validated_data['new_password'])
            user.save()
            
            # Invalidate existing tokens
            Token.objects.filter(user=user).delete()
            
            return Response({'message': 'Password changed successfully'})
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class ResendVerificationEmailView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        user = request.user
        if user.is_verified:
            return Response({"message": "Your email is already verified."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            send_verification_email(user)
            return Response({"message": "Verification email resent successfully."}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response(
                {"error": "Failed to send verification email", "details": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class VerifyEmailView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, uidb64, token):
        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            return Response({"error": "Invalid activation link"}, status=400)

        if default_token_generator.check_token(user, token):
            user.is_verified = True
            user.save()
            return Response({"message": "Email verified successfully"})
        else:
            return Response({"error": "Invalid or expired token"}, status=400)


class PasswordResetRequestView(APIView):
    permission_classes = [permissions.AllowAny]


    @swagger_auto_schema(
        operation_description="Rest your password",
        request_body=PasswordResetRequestSerializer,
        responses={
            200: openapi.Response(
                description="Reset Email successful",
                examples={
                    "application/json": {
            
                        "user": {                            
                            "email": "test@example.com",
                        }
                    }
                }
            ),
            400: "Invalid credentials"
        }
    )
    def post(self, request):
        serializer = PasswordResetRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({"error": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

        email = serializer.validated_data['email']
        try:
            user = User.objects.get(email=email)
            send_password_reset_email(user)
        except User.DoesNotExist:
            # Silently succeed to avoid leaking user existence
            pass

        try:
            send_password_reset_email(user)
            return Response({"message": "If an account with that email exists, a password reset link has been sent."}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response(
                {"error": "Failed to send verification email", "details": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class ResetPasswordConfirmView(APIView):
    permission_classes = [permissions.AllowAny]
    throttle_classes = [AnonRateThrottle]

    def post(self, request):
        serializer = ResetPasswordConfirmSerializer(data=request.data)
        if not serializer.is_valid():
            # Flatten serializer errors into a simple message
            return Response(
                {"error": "Invalid input", "details": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST
            )

        uidb64 = serializer.validated_data['uid']
        token = serializer.validated_data['token']
        
        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            return Response({"error": "Invalid reset link"}, status=status.HTTP_400_BAD_REQUEST)

        if default_token_generator.check_token(user, token):
            user.set_password(serializer.validated_data['new_password'])
            user.save()
            return Response({"message": "Password reset successful"})
        return Response({"error": "Invalid or expired token"}, status=status.HTTP_400_BAD_REQUEST)
    


    
