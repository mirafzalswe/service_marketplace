from celery import shared_task
from django.utils import timezone
from django.contrib.auth import get_user_model
from .models import Order, OrderStatus
import logging

User = get_user_model()
logger = logging.getLogger(__name__)

@shared_task
def send_order_notification(order_id, notification_type):
    """
    Send order-related notifications
    """
    try:
        order = Order.objects.get(id=order_id)
        
        notifications = {
            'order_created': f'New order #{order.id} created by {order.client.username}',
            'order_assigned': f'Order #{order.id} assigned to {order.worker.username if order.worker else "N/A"}',
            'order_completed': f'Order #{order.id} has been completed',
            'order_canceled': f'Order #{order.id} has been canceled'
        }
        
        message = notifications.get(notification_type, 'Order status updated')
        logger.info(f"Order notification: {message}")
        
        # Here you would send actual notifications (email, SMS, push, etc.)
        return message
    
    except Order.DoesNotExist:
        logger.error(f"Order with id {order_id} not found")
        return f"Order not found"
    except Exception as e:
        logger.error(f"Error sending order notification: {e}")
        return f"Error: {e}"

@shared_task
def auto_assign_orders():
    """
    Auto-assign pending orders to available workers
    """
    try:
        pending_orders = Order.objects.filter(status='pending', worker__isnull=True)
        assigned_count = 0
        
        for order in pending_orders:
            # Simple assignment logic - find workers with matching service category
            available_workers = User.objects.filter(
                role='worker',
                is_active=True,
                workerprofile__is_verified=True
            )
            
            if available_workers.exists():
                # For now, just assign to the first available worker
                # In a real system, you'd implement more sophisticated logic
                worker = available_workers.first()
                order.worker = worker
                order.status = 'assigned'
                order.save()
                
                # Create status history
                OrderStatus.objects.create(
                    order=order,
                    status='assigned',
                    comment='Auto-assigned by system',
                    created_by=worker
                )
                
                assigned_count += 1
                
                # Send notification
                send_order_notification.delay(order.id, 'order_assigned')
        
        logger.info(f"Auto-assigned {assigned_count} orders")
        return f"Auto-assigned {assigned_count} orders"
    
    except Exception as e:
        logger.error(f"Error in auto-assignment: {e}")
        return f"Error: {e}"

@shared_task
def cleanup_old_orders():
    """
    Clean up old completed/canceled orders
    """
    try:
        # Delete orders older than 1 year that are completed or canceled
        cutoff_date = timezone.now() - timezone.timedelta(days=365)
        old_orders = Order.objects.filter(
            created_at__lt=cutoff_date,
            status__in=['completed', 'canceled']
        )
        
        count = old_orders.count()
        old_orders.delete()
        
        logger.info(f"Cleaned up {count} old orders")
        return f"Cleaned up {count} old orders"
    
    except Exception as e:
        logger.error(f"Error cleaning up orders: {e}")
        return f"Error: {e}"
