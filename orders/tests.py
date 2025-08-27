from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from .models import Order, OrderStatus
from services.models import Service, ServiceCategory
from accounts.models import User

User = get_user_model()

class OrderModelTest(TestCase):
    def setUp(self):
        # Create test users
        self.client_user = User.objects.create_user(
            username='client',
            email='client@example.com',
            password='clientpass123',
            role='client'
        )
        
        self.worker_user = User.objects.create_user(
            username='worker',
            email='worker@example.com',
            password='workerpass123',
            role='worker'
        )
        
        # Create test service
        self.category = ServiceCategory.objects.create(
            name='Web Development',
            description='All web development services'
        )
        
        self.service = Service.objects.create(
            name='WordPress Website',
            description='Custom WordPress development',
            base_price=500.00,
            category=self.category,
            duration_hours=40
        )
    
    def test_create_order(self):
        order = Order.objects.create(
            client=self.client_user,
            service=self.service,
            description='Need a business website',
            address='123 Main St',
            scheduled_date='2024-01-01 10:00:00',
            total_price=500.00
        )
        self.assertEqual(order.client, self.client_user)
        self.assertEqual(order.service, self.service)
        self.assertEqual(order.status, 'pending')
        self.assertEqual(order.total_price, 500.00)
    
    def test_order_str_method(self):
        order = Order.objects.create(
            client=self.client_user,
            service=self.service,
            description='Need a business website',
            address='123 Main St',
            scheduled_date='2024-01-01 10:00:00',
            total_price=500.00
        )
        expected_str = f"Order #{order.id} - {order.client.username} - {order.service.name}"
        self.assertEqual(str(order), expected_str)

class OrderStatusModelTest(TestCase):
    def setUp(self):
        # Create test users
        self.client_user = User.objects.create_user(
            username='client',
            email='client@example.com',
            password='clientpass123',
            role='client'
        )
        
        self.worker_user = User.objects.create_user(
            username='worker',
            email='worker@example.com',
            password='workerpass123',
            role='worker'
        )
        
        # Create test service and order
        self.category = ServiceCategory.objects.create(
            name='Web Development',
            description='All web development services'
        )
        
        self.service = Service.objects.create(
            name='WordPress Website',
            description='Custom WordPress development',
            base_price=500.00,
            category=self.category,
            duration_hours=40
        )
        
        self.order = Order.objects.create(
            client=self.client_user,
            service=self.service,
            description='Need a business website',
            address='123 Main St',
            scheduled_date='2024-01-01 10:00:00',
            total_price=500.00
        )
    
    def test_create_order_status(self):
        status_update = OrderStatus.objects.create(
            order=self.order,
            status='in_progress',
            comment='Started working on the project',
            created_by=self.worker_user
        )
        self.assertEqual(status_update.order, self.order)
        self.assertEqual(status_update.status, 'in_progress')
        self.assertEqual(status_update.comment, 'Started working on the project')
    
    def test_order_status_str_method(self):
        status_update = OrderStatus.objects.create(
            order=self.order,
            status='in_progress',
            comment='Started working on the project',
            created_by=self.worker_user
        )
        expected_str = f"Order #{self.order.id} - in_progress"
        self.assertEqual(str(status_update), expected_str)

class OrderAPITest(APITestCase):
    def setUp(self):
        self.client = APIClient()
        
        # Create test users
        self.client_user = User.objects.create_user(
            username='client',
            email='client@example.com',
            password='clientpass123',
            role='client'
        )
        
        self.worker_user = User.objects.create_user(
            username='worker',
            email='worker@example.com',
            password='workerpass123',
            role='worker'
        )
        
        self.admin_user = User.objects.create_user(
            username='admin',
            email='admin@example.com',
            password='adminpass123',
            role='admin'
        )
        
        # Create test service
        self.category = ServiceCategory.objects.create(
            name='Web Development',
            description='All web development services'
        )
        
        self.service = Service.objects.create(
            name='WordPress Website',
            description='Custom WordPress development',
            base_price=500.00,
            category=self.category,
            duration_hours=40
        )
        
        # Create test order
        self.order = Order.objects.create(
            client=self.client_user,
            service=self.service,
            description='Need a business website',
            address='123 Main St',
            scheduled_date='2024-01-01 10:00:00',
            total_price=500.00
        )
    
    def get_jwt_token(self, user):
        refresh = RefreshToken.for_user(user)
        return str(refresh.access_token)
    
    def test_order_create_client_only(self):
        token = self.get_jwt_token(self.client_user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        
        url = reverse('order-create')
        data = {
            'service': self.service.id,
            'description': 'Need an e-commerce website',
            'address': '456 Oak St',
            'scheduled_date': '2024-01-15T14:00:00Z',
            'total_price': 800.00
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['description'], 'Need an e-commerce website')
    
    def test_order_create_worker_forbidden(self):
        token = self.get_jwt_token(self.worker_user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        
        url = reverse('order-create')
        data = {
            'service': self.service.id,
            'description': 'Need an e-commerce website',
            'budget': 800.00
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_order_list_authenticated_users(self):
        token = self.get_jwt_token(self.client_user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        
        url = reverse('order-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_order_detail_owner_access(self):
        token = self.get_jwt_token(self.client_user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        
        url = reverse('order-detail', kwargs={'pk': self.order.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['description'], 'Need a business website')
    
    def test_order_assign_worker(self):
        token = self.get_jwt_token(self.worker_user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        
        url = reverse('assign-worker', kwargs={'order_id': self.order.pk})
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Refresh order from database
        self.order.refresh_from_db()
        self.assertEqual(self.order.assigned_worker, self.worker_user)
    
    def test_order_status_update(self):
        # First assign worker
        self.order.assigned_worker = self.worker_user
        self.order.save()
        
        token = self.get_jwt_token(self.worker_user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        
        url = reverse('order-status-update', kwargs={'order_id': self.order.pk})
        data = {
            'status': 'in_progress',
            'comment': 'Started working on the project'
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['status'], 'in_progress')

class OrderStatusAPITest(APITestCase):
    def setUp(self):
        self.client = APIClient()
        
        # Create test users
        self.client_user = User.objects.create_user(
            username='client',
            email='client@example.com',
            password='clientpass123',
            role='client'
        )
        
        self.worker_user = User.objects.create_user(
            username='worker',
            email='worker@example.com',
            password='workerpass123',
            role='worker'
        )
        
        # Create test service and order
        self.category = ServiceCategory.objects.create(
            name='Web Development',
            description='All web development services'
        )
        
        self.service = Service.objects.create(
            name='WordPress Website',
            description='Custom WordPress development',
            base_price=500.00,
            category=self.category,
            duration_hours=40
        )
        
        self.order = Order.objects.create(
            client=self.client_user,
            service=self.service,
            description='Need a business website',
            address='123 Main St',
            scheduled_date='2024-01-01 10:00:00',
            total_price=500.00,
            worker=self.worker_user
        )
    
    def get_jwt_token(self, user):
        refresh = RefreshToken.for_user(user)
        return str(refresh.access_token)
    
    def test_status_update_authorized_users_only(self):
        token = self.get_jwt_token(self.worker_user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        
        url = reverse('order-status-update', kwargs={'order_id': self.order.pk})
        data = {
            'status': 'completed',
            'comment': 'Project completed successfully'
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
