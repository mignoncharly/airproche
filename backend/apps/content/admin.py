from django.contrib import admin

from .models import FAQ, BusinessSettings, LegalDocument, ServiceContent, Testimonial


@admin.register(BusinessSettings)
class BusinessSettingsAdmin(admin.ModelAdmin):
    fieldsets = (
        ("Identity", {"fields": ("business_name", "legal_name", "tagline")}),
        ("Contact", {"fields": ("phone", "whatsapp_phone", "email", "support_hours")}),
        ("Address", {"fields": ("address", "postal_code", "city", "country_code")}),
        (
            "Booking rules",
            {
                "fields": (
                    "currency",
                    "minimum_lead_hours",
                    "maximum_booking_days",
                    "quote_valid_minutes",
                    "booking_enabled",
                )
            },
        ),
    )

    def has_add_permission(self, request):
        return not BusinessSettings.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(ServiceContent)
class ServiceContentAdmin(admin.ModelAdmin):
    list_display = ("title", "slug", "icon", "is_active", "display_order")
    list_editable = ("is_active", "display_order")
    list_filter = ("is_active", "icon")
    prepopulated_fields = {"slug": ("title",)}
    search_fields = ("title", "summary", "description")


@admin.register(FAQ)
class FAQAdmin(admin.ModelAdmin):
    list_display = ("question", "is_active", "display_order", "updated_at")
    list_editable = ("is_active", "display_order")
    list_filter = ("is_active",)
    search_fields = ("question", "answer")


@admin.register(Testimonial)
class TestimonialAdmin(admin.ModelAdmin):
    list_display = (
        "author_name",
        "rating",
        "verified_at",
        "is_active",
        "display_order",
    )
    list_filter = ("is_active", "rating", "verified_at")
    search_fields = ("author_name", "author_context", "quote", "source_reference")
    readonly_fields = ("created_at", "updated_at")


@admin.register(LegalDocument)
class LegalDocumentAdmin(admin.ModelAdmin):
    list_display = ("title", "kind", "version", "effective_at", "is_published")
    list_filter = ("kind", "is_published")
    search_fields = ("title", "body", "version")
