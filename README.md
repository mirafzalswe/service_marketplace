# Service Marketplace

A comprehensive Django REST API platform for connecting service providers with clients. The system enables users to browse services, place orders, and process payments through a secure and scalable architecture.

## Project Overview

Service Marketplace is built with Django REST Framework and provides a complete solution for service-based businesses. The platform supports three user roles: clients who need services, workers who provide services, and administrators who manage the system.

## Key Features

- **User Management** - Role-based authentication system with JWT tokens
- **Service Catalog** - Comprehensive service listings with categories
- **Order Management** - Complete order lifecycle from creation to completion
- **Payment Processing** - Secure payment handling with multiple gateways
- **Real-time Notifications** - WebSocket-based instant updates
- **Asynchronous Tasks** - Background job processing with Celery
- **API Documentation** - Auto-generated Swagger and ReDoc documentation

## System Architecture

### Core Technologies
- Django REST Framework
- JWT Authentication
- Django Channels (WebSocket)
- Celery (Background Tasks)
- Redis (Caching & Message Broker)
- SQLite/PostgreSQL

### Application Structure
- **accounts** - User management and authentication
- **services** - Service catalog and categories
- **orders** - Order processing and status tracking
- **payments** - Payment gateway integration

## API Endpoints

### Authentication Endpoints
- **POST** `/api/auth/register/` - User registration
- **POST** `/api/auth/login/` - User login
- **POST** `/api/auth/refresh/` - JWT token refresh
- **POST** `/api/auth/logout/` - User logout

### User Management
- **GET** `/api/users/` - List all users
- **GET** `/api/users/{id}/` - Get user details
- **PUT** `/api/users/{id}/` - Update user profile
- **GET** `/api/workers/` - List worker profiles
- **GET** `/api/workers/{id}/` - Get worker profile details

### Service Management
- **GET** `/api/services/categories/` - List service categories
- **POST** `/api/services/categories/` - Create category (admin only)
- **GET** `/api/services/` - List available services
- **POST** `/api/services/` - Create new service (worker only)
- **GET** `/api/services/{id}/` - Get service details
- **PUT** `/api/services/{id}/` - Update service information

### Order Management
- **GET** `/api/orders/` - List user orders
- **POST** `/api/orders/create/` - Create new order (client only)
- **GET** `/api/orders/{id}/` - Get order details
- **POST** `/api/orders/{id}/assign/` - Assign worker to order
- **POST** `/api/orders/{id}/status/` - Update order status

### Payment Processing
- **GET** `/api/payments/` - List payment records
- **POST** `/api/payments/order/{order_id}/pay/` - Process payment
- **GET** `/api/payments/{id}/` - Get payment details
- **POST** `/api/payments/{id}/refund/` - Process refund (admin only)

## User Roles & Permissions

### Client Role
- Browse service catalog
- Create and manage orders
- Make payments
- View order history

### Worker Role
- Create and manage services
- Accept assigned orders
- Update order status
- Manage worker profile

### Admin Role
- Full system access
- User management
- Service category management
- Payment refund processing

## Getting Started

### Prerequisites
- Python 3.11 or higher
- Redis server
- Git

### Installation Steps

1. **Clone the repository**
   ```
   git clone <repository-url>
   cd service_marketplace
   ```

2. **Set up virtual environment**
   ```
   pipenv install
   pipenv shell
   ```

3. **Configure environment variables**
   Create a `.env` file with:
   ```
   DEBUG=True
   SECRET_KEY=your-secret-key-here
   REDIS_URL=redis://localhost:6379/0
   ```

4. **Run database migrations**
   ```
   python manage.py migrate
   ```

5. **Create superuser account**
   ```
   python manage.py createsuperuser
   ```

6. **Start the development server**
   ```
   python manage.py runserver
   ```

### Starting Background Services

1. **Start Redis server**
   ```
   redis-server
   ```

2. **Start Celery worker** (in separate terminal)
   ```
   pipenv run celery -A service_marketplace worker -l info
   ```

3. **Start Celery beat scheduler** (in separate terminal)
   ```
   pipenv run celery -A service_marketplace beat -l info
   ```

## Testing

### Running Tests

**Run all tests:**
```
pipenv run python manage.py test
```

**Run specific app tests:**
```
pipenv run python manage.py test accounts
pipenv run python manage.py test services
pipenv run python manage.py test orders
pipenv run python manage.py test payments
```

**Run with verbose output:**
```
pipenv run python manage.py test --verbosity=2
```

### Test Coverage
- **Model Testing** - Database model validation and relationships
- **API Testing** - All endpoint functionality and responses
- **Permission Testing** - Role-based access control
- **Authentication Testing** - JWT token management
- **Payment Testing** - Gateway integration and processing

### Current Test Status
- Total Tests: 49
- Passing: 41 (83.7%)
- Failing: 8 (16.3%)

## API Documentation

Once the server is running, access the interactive API documentation:

- **Swagger UI**: http://localhost:8000/api/schema/swagger-ui/
- **ReDoc**: http://localhost:8000/api/schema/redoc/
- **OpenAPI Schema**: http://localhost:8000/api/schema/

## Development Workflow

### Making Changes
1. Create a feature branch from main
2. Make your changes
3. Write tests for new functionality
4. Run the test suite
5. Update documentation if needed
6. Submit a pull request

### Code Quality
- Follow PEP 8 style guidelines
- Write comprehensive tests
- Add docstrings to functions and classes
- Use meaningful variable and function names

## Production Deployment

### Environment Setup
- Use PostgreSQL instead of SQLite
- Configure proper Redis instance
- Set DEBUG=False
- Use environment variables for sensitive data
- Set up proper logging
- Configure static file serving

### Security Considerations
- Use HTTPS in production
- Configure CORS properly
- Set up firewall rules
- Regular security updates
- Monitor system logs
- Implement rate limiting

## Background Tasks

The system uses Celery for background processing:

### Scheduled Tasks
- **Token Cleanup** - Removes expired JWT tokens (hourly)
- **Order Assignment** - Auto-assigns pending orders (every 5 minutes)
- **Payment Retry** - Retries failed payments (every 30 minutes)
- **Daily Reports** - Generates payment statistics (daily)
- **Data Cleanup** - Removes old completed orders (weekly)

### Manual Task Testing
```
pipenv run python manage.py test_celery
```

## Monitoring & Maintenance

### Health Checks
- API endpoint availability
- Database connectivity
- Redis connection
- Celery worker status

### Log Files
- Application logs in Django
- Celery task logs
- Payment processing logs
- Error tracking and alerts

## Troubleshooting

### Common Issues

**Database Migration Errors**
- Ensure database is accessible
- Check migration files for conflicts
- Run migrations step by step if needed

**Celery Connection Issues**
- Verify Redis is running
- Check REDIS_URL configuration
- Ensure proper firewall settings

**Authentication Problems**
- Check JWT token expiration
- Verify user roles and permissions
- Ensure proper CORS configuration

**Payment Processing Errors**
- Check payment gateway configuration
- Verify test vs production settings
- Monitor payment logs

## Support & Contributing

### Getting Help
- Check the API documentation
- Review existing GitHub issues
- Create a new issue with detailed information

### Contributing Guidelines
- Fork the repository
- Create descriptive commit messages
- Include tests with new features
- Update documentation as needed
- Follow the existing code style

## License

This project is licensed under the MIT License - see the LICENSE file for details.

---

**Project Status**: Active Development  
**Latest Version**: 1.0.0  
**Last Updated**: August 2025
