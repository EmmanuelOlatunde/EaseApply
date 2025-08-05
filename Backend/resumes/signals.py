# resumes/signals.py
import os
import logging
from django.db.models.signals import post_delete, pre_delete
from django.dispatch import receiver
from .models import Resume

logger = logging.getLogger(__name__)

@receiver(pre_delete, sender=Resume)
def delete_resume_file(sender, instance, **kwargs):
    """Delete the physical file when Resume instance is deleted"""
    if instance.file:
        try:
            if os.path.isfile(instance.file.path):
                os.remove(instance.file.path)
                logger.info(f"Deleted file: {instance.file.path}")
        except (FileNotFoundError, OSError) as e:
            logger.warning(f"Could not delete file {instance.file.path}: {e}")

@receiver(post_delete, sender=Resume)
def cleanup_empty_directories(sender, instance, **kwargs):
    """Clean up empty user directories after file deletion"""
    if instance.file:
        try:
            user_dir = os.path.dirname(instance.file.path)
            if os.path.isdir(user_dir) and not os.listdir(user_dir):
                os.rmdir(user_dir)
                logger.info(f"Cleaned up empty directory: {user_dir}")
        except (FileNotFoundError, OSError) as e:
            logger.warning(f"Could not clean up directory: {e}")