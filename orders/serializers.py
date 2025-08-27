from rest_framework import serializers
from .models import Order, OrderStatus
from services.serializers import ServiceSerializer
from accounts.serializers import UserSerializer

class OrderStatusSerializer(serializers.ModelSerializer):
    created_by = UserSerializer(read_only=True)
    
    class Meta:
        model = OrderStatus
        fields = '__all__'

class OrderSerializer(serializers.ModelSerializer):
    service = ServiceSerializer(read_only=True)
    service_id = serializers.IntegerField(write_only=True)
    client = UserSerializer(read_only=True)
    worker = UserSerializer(read_only=True)
    status_history = OrderStatusSerializer(many=True, read_only=True)
    
    class Meta:
        model = Order
        fields = '__all__'
        read_only_fields = ['total_price', 'client']
    
    def create(self, validated_data):
        validated_data['client'] = self.context['request'].user
        return super().create(validated_data)

class OrderCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = ['service', 'description', 'address', 'scheduled_date', 'quantity']
    
    def create(self, validated_data):
        validated_data['client'] = self.context['request'].user
        return super().create(validated_data)