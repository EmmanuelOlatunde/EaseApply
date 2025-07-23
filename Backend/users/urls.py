from django.urls import path
from .views import (
    RegisterView,
    LoginView, 
    LogoutView,
    ProfileView,
    ChangePasswordView,
    ResendVerificationEmailView,
    VerifyEmailView,
    ResetPasswordConfirmView
)

app_name = 'users'

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('profile/', ProfileView.as_view(), name='profile'),
    path('change-password/', ChangePasswordView.as_view(), name='change-password'),
    path('resend-verification/', ResendVerificationEmailView.as_view(), name='resend-verification'),
    path('activate/<uidb64>/<token>/', VerifyEmailView.as_view(), name='email-verify'),
    path('change-password/', ChangePasswordView.as_view(), name='change-password'),
    path('reset-password-confirm/', ResetPasswordConfirmView.as_view(), name='reset-password-confirm'),

]