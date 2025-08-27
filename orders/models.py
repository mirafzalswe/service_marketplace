from django.db import models
from django.contrib.auth import get_user_model
from services.models import Service
from decimal import Decimal

User = get_user_model()

class Order(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('paid', 'Paid'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('canceled', 'Canceled'),
    ]
    
    client = models.ForeignKey(User, on_delete=models.CASCADE, related_name='client_orders')
    worker = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='worker_orders')
    service = models.ForeignKey(Service, on_delete=models.CASCADE)
    
    description = models.TextField()
    address = models.CharField(max_length=500)
    scheduled_date = models.DateTimeField()
    
    quantity = models.PositiveIntegerField(default=1)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Order #{self.id} - {self.client.username} - {self.service.name}"
    
    def save(self, *args, **kwargs):
        if not self.total_price:
            self.total_price = self.service.base_price * Decimal(str(self.quantity))
        super().save(*args, **kwargs)

class OrderStatus(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='status_history')
    status = models.CharField(max_length=20, choices=Order.STATUS_CHOICES)
    comment = models.TextField(blank=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name_plural = "Order Statuses"
    
    def __str__(self):
        return f"Order #{self.order.id} - {self.status}"