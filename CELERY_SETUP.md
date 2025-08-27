# Celery Setup Guide

## Overview
Celery is now properly configured for the Service Marketplace project to handle asynchronous tasks and scheduled jobs.

## Configuration Files Created

### 1. `service_marketplace/celery.py`
- Main Celery application configuration
- Auto-discovery of tasks from Django apps
- Debug task for testing

### 2. `service_marketplace/__init__.py`
- Imports Celery app to ensure it's loaded with Django
- Makes Celery available as `celery_app`

### 3. Task Files Created
- `accounts/tasks.py` - User-related tasks
- `orders/tasks.py` - Order management tasks  
- `payments/tasks.py` - Payment processing tasks

## Available Tasks

### Accounts Tasks
- `cleanup_expired_tokens` - Clean up expired JWT tokens (hourly)
- `send_welcome_email` - Send welcome email to new users
- `update_worker_ratings` - Update worker ratings based on reviews

### Orders Tasks
- `send_order_notification` - Send order-related notifications
- `auto_assign_orders` - Auto-assign pending orders to workers (every 5 min)
- `cleanup_old_orders` - Clean up old completed/canceled orders (weekly)

### Payments Tasks
- `process_payment_async` - Process payments asynchronously
- `send_payment_notification` - Send payment notifications
- `retry_failed_payments` - Retry failed payments (every 30 min)
- `generate_payment_report` - Generate daily payment reports (daily)

## Scheduled Tasks (Celery Beat)

| Task | Schedule | Description |
|------|----------|-------------|
| cleanup_expired_tokens | Every hour | Clean expired JWT tokens |
| auto_assign_orders | Every 5 minutes | Auto-assign pending orders |
| retry_failed_payments | Every 30 minutes | Retry failed payments |
| generate_payment_report | Daily | Generate payment statistics |
| cleanup_old_orders | Weekly | Clean up old orders |

## Running Celery

### Prerequisites
Make sure Redis is running (required for broker and result backend):
```bash
# Install Redis (macOS)
brew install redis
brew services start redis

# Or run Redis manually
redis-server
```

### Start Celery Worker
```bash
# In project directory
pipenv run celery -A service_marketplace worker -l info
```

### Start Celery Beat (Scheduler)
```bash
# In separate terminal
pipenv run celery -A service_marketplace beat -l info
```

### Start Both Worker and Beat Together
```bash
# Single command (for development)
pipenv run celery -A service_marketplace worker -B -l info
```

## Testing Celery

### Test Configuration
```bash
# Test if Celery loads properly
pipenv run python -c "from service_marketplace.celery import app; print('Celery OK:', app)"
```

### Test Tasks via Django Command
```bash
# Run test command
pipenv run python manage.py test_celery
```

### Test Tasks in Django Shell
```python
# Start Django shell
pipenv run python manage.py shell

# Import and run tasks
from accounts.tasks import cleanup_expired_tokens
from payments.tasks import generate_payment_report

# Run synchronously (for testing)
result = cleanup_expired_tokens()
print(result)

# Run asynchronously
task = generate_payment_report.delay()
print(f"Task ID: {task.id}")
print(f"Task Status: {task.status}")
```

## Monitoring

### Celery Flower (Web-based monitoring)
```bash
# Install Flower
pip install flower

# Start Flower
pipenv run celery -A service_marketplace flower
# Access at http://localhost:5555
```

### Command Line Monitoring
```bash
# Monitor active tasks
pipenv run celery -A service_marketplace inspect active

# Monitor registered tasks
pipenv run celery -A service_marketplace inspect registered

# Monitor worker stats
pipenv run celery -A service_marketplace inspect stats
```

## Production Considerations

### Supervisor Configuration
Create `/etc/supervisor/conf.d/celery.conf`:
```ini
[program:celery_worker]
command=/path/to/venv/bin/celery -A service_marketplace worker -l info
directory=/path/to/project
user=www-data
numprocs=1
stdout_logfile=/var/log/celery/worker.log
stderr_logfile=/var/log/celery/worker.log
autostart=true
autorestart=true
startsecs=10

[program:celery_beat]
command=/path/to/venv/bin/celery -A service_marketplace beat -l info
directory=/path/to/project
user=www-data
numprocs=1
stdout_logfile=/var/log/celery/beat.log
stderr_logfile=/var/log/celery/beat.log
autostart=true
autorestart=true
startsecs=10
```

### Environment Variables
```env
# Redis URL for Celery
REDIS_URL=redis://localhost:6379/0

# Celery settings
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0
```

## Troubleshooting

### Common Issues

1. **"Module has no attribute 'celery'"**
   - Ensure `service_marketplace/celery.py` exists
   - Check `service_marketplace/__init__.py` imports

2. **Redis Connection Error**
   - Verify Redis is running: `redis-cli ping`
   - Check REDIS_URL in settings

3. **Tasks Not Executing**
   - Ensure worker is running
   - Check task registration: `celery -A service_marketplace inspect registered`

4. **Beat Schedule Not Working**
   - Ensure beat scheduler is running
   - Check beat database file permissions

### Logs
- Worker logs: Check terminal output or log files
- Beat logs: Check beat scheduler output
- Django logs: Check Django application logs
- Redis logs: Check Redis server logs

## Integration with Views

Tasks can be called from Django views:

```python
from django.http import JsonResponse
from accounts.tasks import send_welcome_email

def register_user(request):
    # ... user creation logic ...
    
    # Send welcome email asynchronously
    send_welcome_email.delay(user.id)
    
    return JsonResponse({'status': 'success'})
```
