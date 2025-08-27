from rest_framework import generics, status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from django.utils import timezone
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from .models import Payment
from .serializers import PaymentSerializer, PaymentCreateSerializer
from .fake_gateway import GATEWAY_MAP
from orders.models import Order
from accounts.permissions import IsClient
import logging

logger = logging.getLogger(__name__)

class PaymentCreateView(APIView):
    permission_classes = [IsClient]
    
    def post(self, request, order_id):
        try:
            order = get_object_or_404(Order, id=order_id, client=request.user)
            
            if order.status != 'pending':
                return Response({'error': 'Order is not in pending status'}, 
                              status=status.HTTP_400_BAD_REQUEST)
            
            if hasattr(order, 'payment'):
                return Response({'error': 'Payment already exists for this order'}, 
                              status=status.HTTP_400_BAD_REQUEST)
            
            serializer = PaymentCreateSerializer(data=request.data)
            if not serializer.is_valid():
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
            payment = Payment.objects.create(
                order=order,
                user=request.user,
                amount=order.total_price,
                payment_method=serializer.validated_data['payment_method']
            )
            
            gateway = GATEWAY_MAP[payment.payment_method]
            
            card_data = None
            if payment.payment_method == 'card':
                card_data = {
                    'card_number': serializer.validated_data['card_number'],
                    'card_expiry': serializer.validated_data['card_expiry'],
                    'card_cvv': serializer.validated_data['card_cvv'],
                    'card_holder_name': serializer.validated_data['card_holder_name'],
                }
            
            try:
                gateway_response = gateway.process_payment(
                    amount=payment.amount,
                    payment_method=payment.payment_method,
                    card_data=card_data
                )
                
                payment.gateway_response = gateway_response
                payment.gateway_transaction_id = gateway_response.get('transaction_id')
                
                if gateway_response['status'] == 'success':
                    payment.status = 'completed'
                    payment.processed_at = timezone.now()
                    order.status = 'paid'
                    order.save()
                    
                    self.send_payment_notification(order, payment, 'payment_success')
                else:
                    payment.status = 'failed'
                    order.status = 'canceled'
                    order.save()
                    
                    # Send failure notification
                    self.send_payment_notification(order, payment, 'payment_failed')
                
                payment.save()
                
                return Response({
                    'payment': PaymentSerializer(payment).data,
                    'gateway_response': gateway_response
                })
                
            except Exception as e:
                logger.error(f"Payment processing error: {e}")
                payment.status = 'failed'
                payment.save()
                
                order.status = 'canceled'
                order.save()
                
                return Response({'error': 'Payment processing failed'}, 
                              status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                
        except Order.DoesNotExist:
            return Response({'error': 'Order not found'}, status=status.HTTP_404_NOT_FOUND)
    
    def send_payment_notification(self, order, payment, notification_type):
        channel_layer = get_channel_layer()
        
        message = {
            'payment_success': f'Payment for order #{order.id} completed successfully',
            'payment_failed': f'Payment for order #{order.id} failed'
        }.get(notification_type)
        
        async_to_sync(channel_layer.group_send)(
            f"user_{order.client.id}",
            {
                'type': 'payment_notification',
                'notification_type': notification_type,
                'order_id': order.id,
                'payment_id': str(payment.id),
                'message': message,
                'amount': str(payment.amount),
                'status': payment.status
            }
        )

class PaymentDetailView(generics.RetrieveAPIView):
    serializer_class = PaymentSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        if self.request.user.role == 'admin':
            return Payment.objects.all()
        else:
            return Payment.objects.filter(user=self.request.user)

class PaymentListView(generics.ListAPIView):
    serializer_class = PaymentSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        if self.request.user.role == 'admin':
            return Payment.objects.all()
        else:
            return Payment.objects.filter(user=self.request.user)

class RefundPaymentView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request, payment_id):
        try:
            payment = get_object_or_404(Payment, id=payment_id)
            
            if request.user.role != 'admin' and payment.user != request.user:
                return Response({'error': 'Permission denied'}, 
                              status=status.HTTP_403_FORBIDDEN)
            
            if payment.status != 'completed':
                return Response({'error': 'Only completed payments can be refunded'}, 
                              status=status.HTTP_400_BAD_REQUEST)
            
            gateway = GATEWAY_MAP[payment.payment_method]
            refund_response = gateway.refund_payment(
                payment.gateway_transaction_id,
                payment.amount
            )
            
            if refund_response['status'] == 'refunded':
                payment.status = 'refunded'
                if payment.gateway_response is None:
                    payment.gateway_response = {}
                payment.gateway_response.update({'refund_data': refund_response})
                payment.save()
                
                payment.order.status = 'canceled'
                payment.order.save()
                
                channel_layer = get_channel_layer()
                async_to_sync(channel_layer.group_send)(
                    f"user_{payment.user.id}",
                    {
                        'type': 'payment_notification',
                        'notification_type': 'payment_refunded',
                        'order_id': payment.order.id,
                        'payment_id': str(payment.id),
                        'message': f'Refund processed for order #{payment.order.id}',
                        'amount': str(payment.amount)
                    }
                )
            
            return Response({
                'payment': PaymentSerializer(payment).data,
                'refund_response': refund_response
            })
            
        except Payment.DoesNotExist:
            return Response({'error': 'Payment not found'}, 
                          status=status.HTTP_404_NOT_FOUND)