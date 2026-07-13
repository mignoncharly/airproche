from django.contrib import admin

from .models import Payment, PaymentAttempt, Refund, WebhookEvent


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ("booking", "provider", "status", "amount", "currency", "environment", "updated_at")
    list_filter = ("provider", "status", "environment")
    search_fields = ("booking__reference", "booking__booker_email", "checkout_session_id", "payment_intent_id")
    readonly_fields = ("public_id", "created_at", "updated_at")


@admin.register(Refund)
class RefundAdmin(admin.ModelAdmin):
    list_display = ("payment", "amount", "currency", "status", "requested_at", "completed_at")
    list_filter = ("status", "currency")
    search_fields = ("payment__booking__reference", "provider_refund_id", "idempotency_key")


for model in (PaymentAttempt, WebhookEvent):
    admin.site.register(model)
