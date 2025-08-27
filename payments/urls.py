from django.urls import path
from .views import PaymentCreateView, PaymentDetailView, PaymentListView, RefundPaymentView

urlpatterns = [
    path('', PaymentListView.as_view(), name='payment-list'),
    path('<uuid:pk>/', PaymentDetailView.as_view(), name='payment-detail'),
    path('order/<int:order_id>/pay/', PaymentCreateView.as_view(), name='payment-create'),
    path('<uuid:payment_id>/refund/', RefundPaymentView.as_view(), name='payment-refund'),
]