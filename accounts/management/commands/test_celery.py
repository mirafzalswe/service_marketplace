from django.core.management.base import BaseCommand
from accounts.tasks import cleanup_expired_tokens, send_welcome_email
from orders.tasks import send_order_notification, auto_assign_orders
from payments.tasks import generate_payment_report
from django.contrib.auth import get_user_model

User = get_user_model()

class Command(BaseCommand):
    help = 'Test Celery tasks'

    def handle(self, *args, **options):
        self.stdout.write('Testing Celery tasks...')
        
        # Test cleanup task
        self.stdout.write('Testing cleanup_expired_tokens...')
        result = cleanup_expired_tokens.delay()
        self.stdout.write(f'Task ID: {result.id}')
        
        # Test welcome email if users exist
        if User.objects.exists():
            user = User.objects.first()
            self.stdout.write(f'Testing send_welcome_email for user {user.id}...')
            result = send_welcome_email.delay(user.id)
            self.stdout.write(f'Task ID: {result.id}')
        
        # Test payment report
        self.stdout.write('Testing generate_payment_report...')
        result = generate_payment_report.delay()
        self.stdout.write(f'Task ID: {result.id}')
        
        self.stdout.write(self.style.SUCCESS('Celery tasks queued successfully!'))
