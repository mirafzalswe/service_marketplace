from django.urls import path
from .views import (
    OrderCreateView, OrderListView, OrderDetailView,
    OrderStatusUpdateView, AssignWorkerView
)

urlpatterns = [
    path('', OrderListView.as_view(), name='order-list'),
    path('create/', OrderCreateView.as_view(), name='order-create'),
    path('<int:pk>/', OrderDetailView.as_view(), name='order-detail'),
    path('<int:order_id>/status/', OrderStatusUpdateView.as_view(), name='order-status-update'),
    path('<int:order_id>/assign/', AssignWorkerView.as_view(), name='assign-worker'),
]