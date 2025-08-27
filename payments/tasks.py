from celery import shared_task
from django.utils import timezone
from django.contrib.auth import get_user_model
from .models import Payment
from .fake_gateway import GATEWAY_MAP
import logging

User = get_user_model()
logger = logging.getLogger(__name__)

@shared_task
def process_payment_async(payment_id):
    """
    Process payment asynchronously
    """
    try:
        payment = Payment.objects.get(id=payment_id)
        
        if payment.status != 'pending':
            return f"Payment {payment_id} is not in pending status"
        
        # Update status to processing
        payment.status = 'processing'
        payment.save()
        
        # Get the appropriate gateway
        gateway = GATEWAY_MAP.get(payment.payment_method)
        if not gateway:
            payment.status = 'failed'
            payment.save()
            return f"No gateway found for payment method: {payment.payment_method}"
        
        # Process payment
        result = gateway.process_payment(
            amount=payment.amount,
            payment_method=payment.payment_method,
            card_data=None  # Would contain actual card data in real implementation
        )
        
        # Update payment based on result
        if result['status'] == 'completed':
            payment.status = 'completed'
            payment.gateway_transaction_id = result['transaction_id']
            payment.gateway_response = result.get('gateway_response', {})
            payment.processed_at = timezone.now()
        else:
            payment.status = 'failed'
            payment.gateway_response = result.get('gateway_response', {})
        
        payment.save()
        
        # Send notification
        send_payment_notification.delay(payment.id, 'payment_processed')
        
        logger.info(f"Payment {payment_id} processed with status: {payment.status}")
        return f"Payment processed: {payment.status}"
    
    except Payment.DoesNotExist:
        logger.error(f"Payment with id {payment_id} not found")
        return f"Payment not found"
    except Exception as e:
        logger.error(f"Error processing payment {payment_id}: {e}")
        return f"Error: {e}"

@shared_task
def send_payment_notification(payment_id, notification_type):
    """
    Send payment-related notifications
    """
    try:
        payment = Payment.objects.get(id=payment_id)
        
        notifications = {
            'payment_processed': f'Payment #{payment.id} for order #{payment.order.id} processed: {payment.status}',
            'payment_refunded': f'Payment #{payment.id} has been refunded',
            'payment_failed': f'Payment #{payment.id} processing failed'
        }
        
        message = notifications.get(notification_type, 'Payment status updated')
        logger.info(f"Payment notification: {message}")
        
        # Here you would send actual notifications
        return message
    
    except Payment.DoesNotExist:
        logger.error(f"Payment with id {payment_id} not found")
        return f"Payment not found"
    except Exception as e:
        logger.error(f"Error sending payment notification: {e}")
        return f"Error: {e}"

@shared_task
def retry_failed_payments():
    """
    Retry failed payments that might be recoverable
    """
    try:
        # Find failed payments from the last 24 hours
        cutoff_time = timezone.now() - timezone.timedelta(hours=24)
        failed_payments = Payment.objects.filter(
            status='failed',
            created_at__gte=cutoff_time
        )
        
        retry_count = 0
        for payment in failed_payments:
            # Only retry if the order is still pending
            if payment.order.status == 'pending':
                process_payment_async.delay(payment.id)
                retry_count += 1
        
        logger.info(f"Queued {retry_count} failed payments for retry")
        return f"Queued {retry_count} payments for retry"
    
    except Exception as e:
        logger.error(f"Error retrying failed payments: {e}")
        return f"Error: {e}"

@shared_task
def generate_payment_report():
    """
    Generate daily payment report
    """
    try:
        today = timezone.now().date()
        payments_today = Payment.objects.filter(created_at__date=today)
        
        stats = {
            'total_payments': payments_today.count(),
            'completed': payments_today.filter(status='completed').count(),
            'failed': payments_today.filter(status='failed').count(),
            'pending': payments_today.filter(status='pending').count(),
            'total_amount': sum(p.amount for p in payments_today.filter(status='completed'))
        }
        
        logger.info(f"Daily payment report: {stats}")
        return f"Payment report generated: {stats}"
    
    except Exception as e:
        logger.error(f"Error generating payment report: {e}")
        return f"Error: {e}"
