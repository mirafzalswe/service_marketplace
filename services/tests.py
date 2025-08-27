from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from .models import ServiceCategory, Service
from accounts.models import User

User = get_user_model()

class ServiceCategoryModelTest(TestCase):
    def setUp(self):
        self.category_data = {
            'name': 'Web Development',
            'description': 'All web development services'
        }
    
    def test_create_service_category(self):
        category = ServiceCategory.objects.create(**self.category_data)
        self.assertEqual(category.name, 'Web Development')
        self.assertEqual(category.description, 'All web development services')
    
    def test_service_category_str_method(self):
        category = ServiceCategory.objects.create(**self.category_data)
        self.assertEqual(str(category), 'Web Development')

class ServiceModelTest(TestCase):
    def setUp(self):
        self.worker_user = User.objects.create_user(
            username='worker',
            email='worker@example.com',
            password='testpass123',
            role='worker'
        )
        
        self.category = ServiceCategory.objects.create(
            name='Web Development',
            description='All web development services'
        )
        
        self.service_data = {
            'name': 'WordPress Website',
            'description': 'Custom WordPress development',
            'base_price': 500.00,
            'category': self.category,
            'duration_hours': 40
        }
    
    def test_create_service(self):
        service = Service.objects.create(**self.service_data)
        self.assertEqual(service.name, 'WordPress Website')
        self.assertEqual(service.base_price, 500.00)
        self.assertEqual(service.category, self.category)
        self.assertTrue(service.is_active)
    
    def test_service_str_method(self):
        service = Service.objects.create(**self.service_data)
        expected_str = f"{service.name} - ${service.base_price}"
        self.assertEqual(str(service), expected_str)

class ServiceAPITest(APITestCase):
    def setUp(self):
        self.client = APIClient()
        
        # Create test users
        self.worker_user = User.objects.create_user(
            username='worker',
            email='worker@example.com',
            password='workerpass123',
            role='worker'
        )
        
        self.client_user = User.objects.create_user(
            username='client',
            email='client@example.com',
            password='clientpass123',
            role='client'
        )
        
        # Create test category
        self.category = ServiceCategory.objects.create(
            name='Web Development',
            description='All web development services'
        )
        
        # Create test service
        self.service = Service.objects.create(
            name='WordPress Website',
            description='Custom WordPress development',
            base_price=500.00,
            category=self.category,
            duration_hours=40
        )
    
    def get_jwt_token(self, user):
        refresh = RefreshToken.for_user(user)
        return str(refresh.access_token)
    
    def test_service_list_public_access(self):
        url = reverse('service-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
    
    def test_service_detail_public_access(self):
        url = reverse('service-detail', kwargs={'pk': self.service.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'WordPress Website')
    
    def test_service_create_worker_only(self):
        token = self.get_jwt_token(self.worker_user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        
        url = reverse('service-list')
        data = {
            'name': 'React App Development',
            'description': 'Custom React application',
            'base_price': 800.00,
            'category_id': self.category.id,
            'duration_hours': 60
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['name'], 'React App Development')
    
    def test_service_create_client_forbidden(self):
        token = self.get_jwt_token(self.client_user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        
        url = reverse('service-list')
        data = {
            'name': 'React App Development',
            'description': 'Custom React application',
            'base_price': 800.00,
            'category_id': self.category.id,
            'duration_hours': 60
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_service_update_owner_only(self):
        token = self.get_jwt_token(self.worker_user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        
        url = reverse('service-detail', kwargs={'pk': self.service.pk})
        data = {'base_price': 600.00}
        response = self.client.patch(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['base_price'], '600.00')

class ServiceCategoryAPITest(APITestCase):
    def setUp(self):
        self.client = APIClient()
        
        self.category1 = ServiceCategory.objects.create(
            name='Web Development',
            description='All web development services'
        )
        
        self.category2 = ServiceCategory.objects.create(
            name='Mobile Development',
            description='Mobile app development services'
        )
    
    def test_category_list_public_access(self):
        url = reverse('service-category-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 4)
