from django.contrib import admin
from .models import Payment

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'amount', 'payment_method', 'status', 'created_at']
    list_filter = ['status', 'payment_method', 'created_at']
    search_fields = ['id', 'user__username', 'gateway_transaction_id']
    readonly_fields = ['id', 'gateway_transaction_id', 'gateway_response', 'created_at', 'updated_at']