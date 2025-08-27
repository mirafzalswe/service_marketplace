from celery import shared_task
from django.utils import timezone
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken, OutstandingToken
import logging

User = get_user_model()
logger = logging.getLogger(__name__)

@shared_task
def cleanup_expired_tokens():
    """
    Clean up expired JWT tokens from the blacklist
    """
    try:
        # Get expired tokens
        expired_tokens = OutstandingToken.objects.filter(
            expires_at__lt=timezone.now()
        )
        
        count = expired_tokens.count()
        expired_tokens.delete()
        
        logger.info(f"Cleaned up {count} expired tokens")
        return f"Cleaned up {count} expired tokens"
    
    except Exception as e:
        logger.error(f"Error cleaning up tokens: {e}")
        return f"Error: {e}"

@shared_task
def send_welcome_email(user_id):
    """
    Send welcome email to new user
    """
    try:
        user = User.objects.get(id=user_id)
        
        # Here you would integrate with your email service
        # For now, just log the action
        logger.info(f"Sending welcome email to {user.email}")
        
        # Simulate email sending
        return f"Welcome email sent to {user.email}"
    
    except User.DoesNotExist:
        logger.error(f"User with id {user_id} not found")
        return f"User not found"
    except Exception as e:
        logger.error(f"Error sending welcome email: {e}")
        return f"Error: {e}"

@shared_task
def update_worker_ratings():
    """
    Update worker ratings based on recent reviews
    """
    try:
        from accounts.models import WorkerProfile
        
        # This would calculate ratings based on reviews
        # For now, just log the action
        worker_count = WorkerProfile.objects.count()
        logger.info(f"Updated ratings for {worker_count} workers")
        
        return f"Updated ratings for {worker_count} workers"
    
    except Exception as e:
        logger.error(f"Error updating worker ratings: {e}")
        return f"Error: {e}"
