from django.contrib import admin

from .models import ContactMessage, EmailDeliveryAttempt, EmailNotification


class EmailDeliveryAttemptInline(admin.TabularInline):
    model = EmailDeliveryAttempt
    extra = 0
    readonly_fields = (
        "attempt_number",
        "request_key",
        "status",
        "provider_response",
        "error_code",
        "error_message",
        "created_at",
    )


@admin.register(EmailNotification)
class EmailNotificationAdmin(admin.ModelAdmin):
    list_display = ("kind", "recipient_email", "status", "last_attempt_at", "created_at")
    list_filter = ("kind", "status", "retryable")
    search_fields = ("recipient_email", "idempotency_key")
    readonly_fields = (
        "public_id",
        "kind",
        "template_key",
        "recipient_email",
        "context",
        "idempotency_key",
        "sent_at",
        "last_attempt_at",
        "created_at",
        "updated_at",
    )
    inlines = (EmailDeliveryAttemptInline,)


@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ("topic", "email", "status", "assigned_to", "created_at")
    list_filter = ("topic", "status")
    search_fields = ("email", "first_name", "last_name", "message")
    readonly_fields = (
        "public_id",
        "first_name",
        "last_name",
        "email",
        "phone",
        "topic",
        "message",
        "source_fingerprint",
        "idempotency_key",
        "request_hash",
        "created_at",
        "updated_at",
    )
