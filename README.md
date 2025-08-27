# Service Marketplace - Documentation

## Project Overview

Service Marketplace is a Django REST Framework-based web application for managing services, orders, and payments. The system supports three types of users: clients, workers, and administrators.

## System Architecture

### Core Components

- **Django REST Framework** - Main API framework
- **JWT Authentication** - User authentication system
- **Django Channels** - Real-time WebSocket notifications
- **SQLite** - Database (for development)
- **Celery** - Asynchronous task processing
- **drf-spectacular** - Automatic API documentation generation

### Application Structure

```
service_marketplace/
├── accounts/          # User management
├── services/          # Service catalog
├── orders/           # Order management
├── payments/         # Payment processing
└── service_marketplace/  # Core settings
```

## Data Models

### Users (accounts)

#### User (Custom User Model)
```python
class User(AbstractUser):
    ROLE_CHOICES = [
        ('client', 'Client'),
        ('worker', 'Worker'), 
        ('admin', 'Admin'),
    ]
    role = CharField(choices=ROLE_CHOICES, default='client')
    phone_number = CharField(max_length=15, blank=True)
    date_of_birth = DateField(null=True, blank=True)
    avatar = ImageField(upload_to='avatars/', null=True, blank=True)
```

#### WorkerProfile
```python
class WorkerProfile(Model):
    user = OneToOneField(User, on_delete=CASCADE)
    bio = TextField(blank=True)
    skills = TextField(blank=True)
    hourly_rate = DecimalField(max_digits=8, decimal_places=2, null=True)
    rating = DecimalField(max_digits=3, decimal_places=2, default=0.00)
    total_reviews = PositiveIntegerField(default=0)
    is_verified = BooleanField(default=False)
```

### Services (services)

#### ServiceCategory
```python
class ServiceCategory(Model):
    name = CharField(max_length=100, unique=True)
    description = TextField(blank=True)
    icon = CharField(max_length=50, blank=True)
```

#### Service
```python
class Service(Model):
    name = CharField(max_length=200)
    description = TextField()
    category = ForeignKey(ServiceCategory, on_delete=CASCADE)
    base_price = DecimalField(max_digits=10, decimal_places=2)
    duration_hours = PositiveIntegerField()
    is_active = BooleanField(default=True)
    created_at = DateTimeField(auto_now_add=True)
```

### Orders (orders)

#### Order
```python
class Order(Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('assigned', 'Assigned'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('canceled', 'Canceled'),
    ]
    
    client = ForeignKey(User, on_delete=CASCADE, related_name='client_orders')
    worker = ForeignKey(User, on_delete=SET_NULL, null=True, related_name='worker_orders')
    service = ForeignKey(Service, on_delete=CASCADE)
    description = TextField()
    address = CharField(max_length=255)
    scheduled_date = DateTimeField()
    quantity = PositiveIntegerField(default=1)
    total_price = DecimalField(max_digits=10, decimal_places=2)
    status = CharField(choices=STATUS_CHOICES, default='pending')
```

#### OrderStatus
```python
class OrderStatus(Model):
    order = ForeignKey(Order, on_delete=CASCADE, related_name='status_history')
    status = CharField(choices=Order.STATUS_CHOICES)
    comment = TextField(blank=True)
    created_by = ForeignKey(User, on_delete=CASCADE)
    created_at = DateTimeField(auto_now_add=True)
```

### Payments (payments)

#### Payment
```python
class Payment(Model):
    PAYMENT_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('canceled', 'Canceled'),
        ('refunded', 'Refunded'),
    ]
    
    PAYMENT_METHOD_CHOICES = [
        ('payme', 'Payme'),
        ('click', 'Click'),
        ('card', 'Credit Card'),
    ]
    
    id = UUIDField(primary_key=True, default=uuid4)
    order = OneToOneField(Order, on_delete=CASCADE)
    user = ForeignKey(User, on_delete=CASCADE)
    amount = DecimalField(max_digits=10, decimal_places=2)
    currency = CharField(max_length=3, default='USD')
    payment_method = CharField(choices=PAYMENT_METHOD_CHOICES)
    status = CharField(choices=PAYMENT_STATUS_CHOICES, default='pending')
    gateway_transaction_id = CharField(max_length=255, blank=True, null=True)
    gateway_response = JSONField(blank=True, null=True)
```

## API Endpoints

### Authentication
- `POST /api/auth/register/` - User registration
- `POST /api/auth/login/` - User login
- `POST /api/auth/refresh/` - JWT token refresh
- `POST /api/auth/logout/` - User logout

### Users
- `GET /api/users/` - List users
- `GET /api/users/{id}/` - User details
- `PUT /api/users/{id}/` - Update profile
- `GET /api/workers/` - List workers
- `GET /api/workers/{id}/` - Worker profile

### Services
- `GET /api/services/categories/` - Service categories
- `POST /api/services/categories/` - Create category (admin only)
- `GET /api/services/` - List services
- `POST /api/services/` - Create service (worker only)
- `GET /api/services/{id}/` - Service details
- `PUT /api/services/{id}/` - Update service

### Orders
- `GET /api/orders/` - List orders
- `POST /api/orders/create/` - Create order (client only)
- `GET /api/orders/{id}/` - Order details
- `POST /api/orders/{id}/assign/` - Assign worker
- `POST /api/orders/{id}/status/` - Update order status

### Payments
- `GET /api/payments/` - List payments
- `POST /api/payments/order/{order_id}/pay/` - Create payment
- `GET /api/payments/{id}/` - Payment details
- `POST /api/payments/{id}/refund/` - Process refund (admin only)

## Permission System

### User Roles

#### Client
- Create orders
- View own orders
- Make payments
- Browse service catalog

#### Worker
- Create services
- Accept orders
- Update order status
- Manage worker profile

#### Admin
- Full system access
- Manage service categories
- Process refunds
- Content moderation

### Custom Permissions

```python
class IsOwnerOrAdmin(BasePermission):
    def has_object_permission(self, request, view, obj):
        return obj == request.user or request.user.role == 'admin'

class IsWorker(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'worker'

class IsClient(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'client'
```

## WebSocket Notifications

The system supports real-time notifications via WebSocket:

### Connection
```javascript
const socket = new WebSocket('ws://localhost:8000/ws/notifications/');
```

### Notification Types
- `order_created` - New order created
- `order_assigned` - Order assigned to worker
- `order_status_changed` - Order status updated
- `payment_success` - Payment processed successfully
- `payment_failed` - Payment processing failed

## Payment System

### Supported Methods
- **Payme** - Uzbek payment system
- **Click** - Uzbek payment system  
- **Credit Card** - Bank cards

### Fake Payment Gateway
For testing purposes, a fake payment gateway is implemented:

```python
class FakePaymentGateway:
    def process_payment(self, amount, payment_method, card_data=None):
        # Simulate payment processing
        success_rate = 0.8  # 80% success rate
        
        if random.random() < success_rate:
            return {
                'status': 'completed',
                'transaction_id': str(uuid.uuid4()),
                'gateway_response': {...}
            }
        else:
            return {
                'status': 'failed',
                'transaction_id': None,
                'gateway_response': {...}
            }
```

## Testing

### Test Structure
```
tests/
├── accounts/tests.py      # User tests
├── services/tests.py      # Service tests
├── orders/tests.py        # Order tests
└── payments/tests.py      # Payment tests
```

### Running Tests
```bash
# All tests
pipenv run python manage.py test

# Specific app
pipenv run python manage.py test accounts

# Verbose output
pipenv run python manage.py test --verbosity=2
```

### Test Coverage
- **Models** - Creation and validation testing
- **API** - All endpoint testing
- **Permissions** - Role-based access verification
- **Authentication** - JWT token functionality
- **Payment Gateway** - External service mocking

## Deployment

### Requirements
```
Python 3.11+
Django 4.2+
PostgreSQL (for production)
Redis (for Celery and Channels)
```

### Installation
```bash
# Create virtual environment
pipenv install

# Activate environment
pipenv shell

# Database migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser
```

### Environment Variables
```env
DEBUG=True
SECRET_KEY=your-secret-key
DATABASE_URL=sqlite:///db.sqlite3
REDIS_URL=redis://localhost:6379/0
ALLOWED_HOSTS=localhost,127.0.0.1
```

### Running the Server
```bash
# Django server
python manage.py runserver

# Celery worker (separate terminal)
celery -A service_marketplace worker -l info

# Celery beat (task scheduler)
celery -A service_marketplace beat -l info
```

## API Documentation

Automatic API documentation is available at:
- **Swagger UI**: `/api/schema/swagger-ui/`
- **ReDoc**: `/api/schema/redoc/`
- **OpenAPI Schema**: `/api/schema/`

## Security

### Implemented Measures
- JWT authentication with refresh tokens
- Role-based access control (RBAC)
- Input data validation
- CORS configuration
- CSRF protection
- Password hashing (Django default)

### Production Recommendations
- Use HTTPS
- Configure firewall
- Regular dependency updates
- Security log monitoring
- Database backups

## Monitoring and Logging

### Logging Configuration
```python
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': 'service_marketplace.log',
        },
    },
    'loggers': {
        'payments': {
            'handlers': ['file'],
            'level': 'INFO',
            'propagate': True,
        },
    },
}
```

### Monitoring Metrics
- Active user count
- Order status distribution
- Payment success rate
- API response times
- System errors

## Development Status

### Test Results
- **Total Tests**: 49
- **Passing**: 41 ✅ (83.7%)
- **Failing**: 8 ❌ (16.3%)

### Recent Fixes Applied
- ✅ Fixed model field mismatches in tests
- ✅ Corrected URL pattern issues
- ✅ Updated payment gateway integration
- ✅ Fixed JWT authentication in tests
- ✅ Implemented role-based permissions
- ✅ Resolved serializer validation issues

### Remaining Issues
- Payment creation validation (HTTP 400 errors)
- Order status update permissions
- Payment refund response structure
- Order worker assignment endpoints

## Roadmap

### Planned Features
- [ ] Review and rating system
- [ ] Client-worker chat functionality
- [ ] Mobile application
- [ ] Real payment gateway integration
- [ ] Discount and promo code system
- [ ] Analytics and reporting
- [ ] Multi-language support
- [ ] Geolocation-based services

### Technical Improvements
- [ ] Redis caching implementation
- [ ] Database query optimization
- [ ] Docker containerization
- [ ] CI/CD pipeline setup
- [ ] Automated testing
- [ ] Performance monitoring

## Contributing

### Development Setup
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass
6. Submit a pull request

### Code Standards
- Follow PEP 8 style guidelines
- Write comprehensive tests
- Document new features
- Use meaningful commit messages

## Support

For help or bug reports:
- Create an issue in the repository
- Contact the development team
- Check the API documentation

## License

This project is licensed under the MIT License. See the LICENSE file for details.

---

**Last Updated**: August 2025  
**Version**: 1.0.0  
**Status**: Development
