from django.urls import path

from .views import (
    BookingPaymentStatusView, PaymentCheckoutView, PaymentReconcileView,
    PaymentRefundView, StripeWebhookView,
)

app_name = "payments"

urlpatterns = [
    path("bookings/<uuid:booking_public_id>/checkout/", PaymentCheckoutView.as_view(), name="checkout"),
    path("bookings/<uuid:booking_public_id>/status/", BookingPaymentStatusView.as_view(), name="booking-status"),
    path("<uuid:public_id>/reconcile/", PaymentReconcileView.as_view(), name="reconcile"),
    path("<uuid:public_id>/refund/", PaymentRefundView.as_view(), name="refund"),
    path("webhooks/stripe/", StripeWebhookView.as_view(), name="stripe-webhook"),
]
