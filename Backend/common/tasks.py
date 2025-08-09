from celery import shared_task
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.conf import settings
import logging

logger = logging.getLogger(__name__)
@shared_task(bind=True, max_retries=3)
def send_verification_email_task(self, user_id):
    from django.contrib.auth import get_user_model
    User = get_user_model()
    user = User.objects.get(pk=user_id)
    
    try:
        token = default_token_generator.make_token(user)
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        
        subject = 'Verify your email'
        html_message = render_to_string('email/verification_email.html', {
            'user': user,
            'uid': uid,
            'token': token,
            'domain': settings.FRONTEND_URL
        })
        
        send_mail(subject, '', settings.DEFAULT_FROM_EMAIL, [user.email], html_message=html_message)
    except Exception as exc:
        raise self.retry(exc=exc, countdown=60)  # Retry after 1 min


@shared_task(bind=True, max_retries=3)
def send_password_reset_email_task(self, user_id):
    from django.contrib.auth import get_user_model
    User = get_user_model()
    user = User.objects.get(pk=user_id)

    cache_key = f"email:password_reset:{user.id}"
    from common.redis_service import app_cache    # import your redis cache instance here
    
    # Check cache to prevent spamming
    if app_cache.redis.exists(cache_key):
        logger.info(f"⏳ Skipping password reset email to {user.email} (cached recently)")
        return

    try:
        token = default_token_generator.make_token(user)
        uid = urlsafe_base64_encode(force_bytes(user.pk))

        subject = 'Password Reset'
        html_message = render_to_string('email/password_reset.html', {
            'user': user,
            'uid': uid,
            'token': token,
            'domain': settings.FRONTEND_URL,
        })

        send_mail(subject, '', settings.DEFAULT_FROM_EMAIL, [user.email], html_message=html_message)

        # Cache for 5 minutes to avoid resending too fast
        app_cache.redis.set(cache_key, True, timeout=300)

        logger.info(f"✅ Password reset email sent to {user.email}")
    except Exception as exc:
        logger.error(f"Failed to send password reset email: {exc}", exc_info=True)
        raise self.retry(exc=exc, countdown=60)  # Retry after 1 min