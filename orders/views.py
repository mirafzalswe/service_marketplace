from rest_framework import generics, status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from django.db.models import Q
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from drf_spectacular.utils import extend_schema, extend_schema_view
from .models import Order, OrderStatus
from .serializers import OrderSerializer, OrderCreateSerializer, OrderStatusSerializer
from accounts.permissions import IsAdmin, IsClient, IsWorker
from services.models import Service
import logging

logger = logging.getLogger(__name__)

class OrderCreateView(generics.CreateAPIView):
    serializer_class = OrderCreateSerializer
    permission_classes = [IsClient]
    
    def perform_create(self, serializer):
        order = serializer.save()
        
        # Send real-time notification
        self.send_order_notification(order, 'order_created')
        
        return order
    
    def send_order_notification(self, order, notification_type):
        channel_layer = get_channel_layer()
        
        # Notify client
        async_to_sync(channel_layer.group_send)(
            f"user_{order.client.id}",
            {
                'type': 'order_notification',
                'notification_type': notification_type,
                'order_id': order.id,
                'message': f'Order #{order.id} has been created successfully',
                'data': OrderSerializer(order).data
            }
        )
        
        # Notify workers with matching specialization
        workers = order.service.workers.filter(is_available=True)
        for worker in workers:
            async_to_sync(channel_layer.group_send)(
                f"user_{worker.user.id}",
                {
                    'type': 'order_notification',
                    'notification_type': 'new_order_available',
                    'order_id': order.id,
                    'message': f'New order available: {order.service.name}',
                    'data': OrderSerializer(order).data
                }
            )

class OrderListView(generics.ListAPIView):
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        
        if user.role == 'admin':
            return Order.objects.all()
        elif user.role == 'client':
            return Order.objects.filter(client=user)
        elif user.role == 'worker':
            # Worker sees orders for their specializations
            worker_services = user.worker_profile.specializations.all()
            return Order.objects.filter(service__in=worker_services)
        
        return Order.objects.none()

class OrderDetailView(generics.RetrieveUpdateAPIView):
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        
        if user.role == 'admin':
            return Order.objects.all()
        elif user.role == 'client':
            return Order.objects.filter(client=user)
        elif user.role == 'worker':
            worker_services = user.worker_profile.specializations.all()
            return Order.objects.filter(service__in=worker_services)
        
        return Order.objects.none()

class OrderStatusUpdateView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request, order_id):
        try:
            order = Order.objects.get(id=order_id)
            new_status = request.data.get('status')
            comment = request.data.get('comment', '')
            
            # Permission check
            if request.user.role == 'client' and order.client != request.user:
                return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)
            elif request.user.role == 'worker' and order.worker != request.user:
                return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)
            
            # Update order status
            order.status = new_status
            order.save()
            
            # Create status history
            OrderStatus.objects.create(
                order=order,
                status=new_status,
                comment=comment,
                created_by=request.user
            )
            
            # Send real-time notification
            self.send_status_update_notification(order, new_status, comment)
            
            return Response(OrderSerializer(order).data)
            
        except Order.DoesNotExist:
            return Response({'error': 'Order not found'}, status=status.HTTP_404_NOT_FOUND)
    
    def send_status_update_notification(self, order, new_status, comment):
        channel_layer = get_channel_layer()
        
        # Notify client
        async_to_sync(channel_layer.group_send)(
            f"user_{order.client.id}",
            {
                'type': 'status_update',
                'order_id': order.id,
                'new_status': new_status,
                'comment': comment,
                'message': f'Order #{order.id} status updated to {new_status}'
            }
        )
        
        # Notify worker if assigned
        if order.worker:
            async_to_sync(channel_layer.group_send)(
                f"user_{order.worker.id}",
                {
                    'type': 'status_update',
                    'order_id': order.id,
                    'new_status': new_status,
                    'comment': comment,
                    'message': f'Order #{order.id} status updated to {new_status}'
                }
            )

class AssignWorkerView(APIView):
    permission_classes = [IsWorker]
    
    def post(self, request, order_id):
        try:
            order = Order.objects.get(id=order_id, status='paid')
            
            # Check if worker has the required specialization
            if not request.user.worker_profile.specializations.filter(id=order.service.id).exists():
                return Response({'error': 'You are not specialized in this service'}, 
                              status=status.HTTP_400_BAD_REQUEST)
            
            if order.worker:
                return Response({'error': 'Order already assigned'}, 
                              status=status.HTTP_400_BAD_REQUEST)
            
            order.worker = request.user
            order.status = 'in_progress'
            order.save()
            
            # Create status history
            OrderStatus.objects.create(
                order=order,
                status='in_progress',
                comment=f'Assigned to {request.user.get_full_name() or request.user.username}',
                created_by=request.user
            )
            
            # Send notification
            channel_layer = get_channel_layer()
            async_to_sync(channel_layer.group_send)(
                f"user_{order.client.id}",
                {
                    'type': 'order_notification',
                    'notification_type': 'worker_assigned',
                    'order_id': order.id,
                    'message': f'Worker assigned to your order #{order.id}',
                    'worker_name': request.user.get_full_name() or request.user.username
                }
            )
            
            return Response(OrderSerializer(order).data)
            
        except Order.DoesNotExist:
            return Response({'error': 'Order not found'}, status=status.HTTP_404_NOT_FOUND)