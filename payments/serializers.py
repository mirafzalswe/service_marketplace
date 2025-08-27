from rest_framework import serializers
from .models import Payment

class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = '__all__'
        read_only_fields = ['id', 'gateway_transaction_id', 'gateway_response', 
                           'processed_at', 'created_at', 'updated_at']

class PaymentCreateSerializer(serializers.Serializer):
    payment_method = serializers.ChoiceField(choices=Payment.PAYMENT_METHOD_CHOICES)
    card_number = serializers.CharField(max_length=19, required=False)
    card_expiry = serializers.CharField(max_length=5, required=False)  # MM/YY
    card_cvv = serializers.CharField(max_length=4, required=False)
    card_holder_name = serializers.CharField(max_length=100, required=False)
    
    def validate(self, attrs):
        payment_method = attrs.get('payment_method')
        
        if payment_method == 'card':
            required_fields = ['card_number', 'card_expiry', 'card_cvv', 'card_holder_name']
            for field in required_fields:
                if not attrs.get(field):
                    raise serializers.ValidationError(f'{field} is required for card payments')
        
        return attrs