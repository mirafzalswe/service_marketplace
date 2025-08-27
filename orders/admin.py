from django.contrib import admin
from .models import Order, OrderStatus

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['id', 'client', 'worker', 'service', 'status', 'total_price', 'created_at']
    list_filter = ['status', 'service__category', 'created_at']
    search_fields = ['client__username', 'worker__username', 'service__name']
    readonly_fields = ['total_price', 'created_at', 'updated_at']

@admin.register(OrderStatus)
class OrderStatusAdmin(admin.ModelAdmin):
    list_display = ['order', 'status', 'created_by', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['order__id']
    readonly_fields = ['created_at']