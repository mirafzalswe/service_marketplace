from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from unittest.mock import patch, MagicMock
from .models import Payment
from orders.models import Order
from services.models import Service, ServiceCategory
from accounts.models import User

User = get_user_model()

class PaymentModelTest(TestCase):
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
            total_price=500.00,
            status='pending'
        )
    
    def test_create_payment(self):
        payment = Payment.objects.create(
            order=self.order,
            user=self.client_user,
            amount=500.00,
            payment_method='card',
            gateway_transaction_id='txn_123456789'
        )
        self.assertEqual(payment.order, self.order)
        self.assertEqual(payment.amount, 500.00)
        self.assertEqual(payment.status, 'pending')
        self.assertEqual(payment.payment_method, 'card')
    
    def test_payment_str_method(self):
        payment = Payment.objects.create(
            order=self.order,
            user=self.client_user,
            amount=500.00,
            payment_method='card',
            gateway_transaction_id='txn_123456789'
        )
        expected_str = f"Payment {payment.id} - {payment.amount} - {payment.status}"
        self.assertEqual(str(payment), expected_str)

class PaymentAPITest(APITestCase):
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
            status='pending'
        )
        
        # Create test payment
        self.payment = Payment.objects.create(
            order=self.order,
            user=self.client_user,
            amount=500.00,
            payment_method='card',
            gateway_transaction_id='txn_123456789'
        )
    
    def get_jwt_token(self, user):
        refresh = RefreshToken.for_user(user)
        return str(refresh.access_token)
    
    def test_payment_list_authenticated_users(self):
        token = self.get_jwt_token(self.client_user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        
        url = reverse('payment-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_payment_detail_owner_access(self):
        token = self.get_jwt_token(self.client_user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        
        url = reverse('payment-detail', kwargs={'pk': self.payment.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['amount'], '500.00')
    
    @patch('payments.fake_gateway.FakePaymentGateway.process_payment')
    def test_create_payment_success(self, mock_process):
        # Mock successful payment processing
        mock_process.return_value = {
            'status': 'completed',
            'transaction_id': 'txn_987654321',
            'gateway_response': {'message': 'Payment processed successfully'}
        }
        
        token = self.get_jwt_token(self.client_user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        
        url = reverse('payment-create', kwargs={'order_id': self.order.id})
        data = {
            'payment_method': 'card',
            'card_number': '4111111111111111',
            'card_expiry': '12/25',
            'card_cvv': '123',
            'card_holder_name': 'John Doe'
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['status'], 'completed')
    
    @patch('payments.fake_gateway.FakePaymentGateway.process_payment')
    def test_create_payment_failure(self, mock_process):
        # Mock failed payment processing
        mock_process.return_value = {
            'status': 'failed',
            'transaction_id': None,
            'gateway_response': {'message': 'Payment failed - insufficient funds'}
        }
        
        token = self.get_jwt_token(self.client_user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        
        url = reverse('payment-create', kwargs={'order_id': self.order.id})
        data = {
            'payment_method': 'card',
            'card_number': '4111111111111111',
            'card_expiry': '12/25',
            'card_cvv': '123',
            'card_holder_name': 'John Doe'
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['status'], 'failed')
    
    def test_create_payment_unauthorized(self):
        url = reverse('payment-create', kwargs={'order_id': self.order.id})
        data = {
            'payment_method': 'card',
            'card_number': '4111111111111111',
            'card_expiry': '12/25',
            'card_cvv': '123',
            'card_holder_name': 'John Doe'
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    @patch('payments.fake_gateway.FakePaymentGateway.refund_payment')
    def test_refund_payment_success(self, mock_refund):
        # Set payment to completed first
        self.payment.status = 'completed'
        self.payment.save()
        
        # Mock successful refund processing
        mock_refund.return_value = {
            'status': 'refunded',
            'refund_id': 'ref_123456789',
            'original_transaction_id': 'txn_123456789',
            'refunded_amount': 'full'
        }
        
        token = self.get_jwt_token(self.admin_user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        
        url = reverse('payment-refund', kwargs={'payment_id': self.payment.pk})
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'refunded')
    
    @patch('payments.fake_gateway.FakePaymentGateway.refund_payment')
    def test_refund_payment_failure(self, mock_refund):
        # Set payment to completed first
        self.payment.status = 'completed'
        self.payment.save()
        
        # Mock failed refund processing
        mock_refund.return_value = {
            'status': 'failed',
            'refund_id': None,
            'original_transaction_id': 'txn_123456789',
            'refunded_amount': None
        }
        
        token = self.get_jwt_token(self.admin_user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        
        url = reverse('payment-refund', kwargs={'payment_id': self.payment.pk})
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_refund_payment_client_forbidden(self):
        token = self.get_jwt_token(self.client_user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        
        url = reverse('payment-refund', kwargs={'payment_id': self.payment.pk})
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

class FakePaymentGatewayTest(TestCase):
    def setUp(self):
        from .fake_gateway import FakePaymentGateway
        self.gateway = FakePaymentGateway()
    
    def test_process_payment_structure(self):
        result = self.gateway.process_payment(100.00, 'card', 'card_123')
        
        # Check that result has required keys
        self.assertIn('status', result)
        self.assertIn('transaction_id', result)
        self.assertIn('gateway_response', result)
        
        # Check that status is string
        self.assertIsInstance(result['status'], str)
    
    def test_verify_payment_structure(self):
        result = self.gateway.verify_payment('txn_123456789')
        
        # Check that result has required keys
        self.assertIn('status', result)
        self.assertIn('transaction_id', result)
        self.assertIn('verified', result)
        
        # Check that verified is boolean
        self.assertIsInstance(result['verified'], bool)
    
    def test_process_refund_structure(self):
        result = self.gateway.refund_payment('txn_123456789', 100.00)
        
        # Check that result has required keys
        self.assertIn('status', result)
        self.assertIn('refund_id', result)
        self.assertIn('original_transaction_id', result)
        
        # Check that status is string
        self.assertIsInstance(result['status'], str)
