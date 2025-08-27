from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from .models import User, WorkerProfile
from .serializers import UserSerializer, WorkerProfileSerializer

User = get_user_model()

class UserModelTest(TestCase):
    def setUp(self):
        self.user_data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'testpass123',
            'role': 'client',
            'first_name': 'Test',
            'last_name': 'User'
        }
    
    def test_create_user(self):
        user = User.objects.create_user(**self.user_data)
        self.assertEqual(user.username, 'testuser')
        self.assertEqual(user.email, 'test@example.com')
        self.assertEqual(user.role, 'client')
        self.assertTrue(user.check_password('testpass123'))
        self.assertFalse(user.is_verified)
    
    def test_create_worker_user(self):
        self.user_data['role'] = 'worker'
        user = User.objects.create_user(**self.user_data)
        self.assertEqual(user.role, 'worker')
    
    def test_user_str_method(self):
        user = User.objects.create_user(**self.user_data)
        expected_str = f"{user.username} ({user.role})"
        self.assertEqual(str(user), expected_str)

class WorkerProfileModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='worker1',
            email='worker@example.com',
            password='testpass123',
            role='worker'
        )
    
    def test_create_worker_profile(self):
        profile = WorkerProfile.objects.create(
            user=self.user,
            experience_years=5,
            hourly_rate=25.00,
            bio='Experienced worker'
        )
        self.assertEqual(profile.user, self.user)
        self.assertEqual(profile.experience_years, 5)
        self.assertEqual(profile.hourly_rate, 25.00)
        self.assertTrue(profile.is_available)
    
    def test_worker_profile_str_method(self):
        profile = WorkerProfile.objects.create(user=self.user)
        expected_str = f"{self.user.username} - Worker Profile"
        self.assertEqual(str(profile), expected_str)

class AuthenticationAPITest(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.register_url = reverse('register')
        self.login_url = reverse('login')
        
        self.user_data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'testpass123',
            'role': 'client',
            'first_name': 'Test',
            'last_name': 'User'
        }
    
    def test_user_registration(self):
        response = self.client.post(self.register_url, self.user_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(User.objects.filter(username='testuser').exists())
    
    def test_user_registration_duplicate_username(self):
        User.objects.create_user(**self.user_data)
        response = self.client.post(self.register_url, self.user_data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('username', response.data)
    
    def test_user_login(self):
        User.objects.create_user(**self.user_data)
        login_data = {
            'username': 'testuser',
            'password': 'testpass123'
        }
        response = self.client.post(self.login_url, login_data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)
        self.assertIn('user', response.data)
    
    def test_user_login_invalid_credentials(self):
        User.objects.create_user(**self.user_data)
        login_data = {
            'username': 'testuser',
            'password': 'wrongpassword'
        }
        response = self.client.post(self.login_url, login_data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

class UserAPITest(APITestCase):
    def setUp(self):
        self.client = APIClient()
        
        # Create test users
        self.admin_user = User.objects.create_user(
            username='admin',
            email='admin@example.com',
            password='adminpass123',
            role='admin'
        )
        
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
    
    def get_jwt_token(self, user):
        refresh = RefreshToken.for_user(user)
        return str(refresh.access_token)
    
    def test_user_list_admin_access(self):
        token = self.get_jwt_token(self.admin_user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        
        url = reverse('user-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 3)
    
    def test_user_list_client_access_denied(self):
        token = self.get_jwt_token(self.client_user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        
        url = reverse('user-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_user_detail_owner_access(self):
        token = self.get_jwt_token(self.client_user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        
        url = reverse('user-detail', kwargs={'pk': self.client_user.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['username'], 'client')

class WorkerProfileAPITest(APITestCase):
    def setUp(self):
        self.client = APIClient()
        
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
    
    def get_jwt_token(self, user):
        refresh = RefreshToken.for_user(user)
        return str(refresh.access_token)
    
    def test_worker_profile_access(self):
        token = self.get_jwt_token(self.worker_user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        
        url = reverse('worker-profile')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_worker_profile_client_access_denied(self):
        token = self.get_jwt_token(self.client_user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        
        url = reverse('worker-profile')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_worker_profile_update(self):
        token = self.get_jwt_token(self.worker_user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        
        url = reverse('worker-profile')
        data = {
            'experience_years': 3,
            'hourly_rate': 30.00,
            'bio': 'Updated bio'
        }
        response = self.client.patch(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['experience_years'], 3)
