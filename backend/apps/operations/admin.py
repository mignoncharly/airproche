from django.contrib import admin

from .models import AuditEvent, Driver, DriverAssignment, DriverInquiry, MarketplaceDriverProfile, Vehicle


@admin.register(Driver)
class DriverAdmin(admin.ModelAdmin):
    list_display = ("name", "phone", "active", "max_passengers", "updated_at")
    list_filter = ("active",)
    search_fields = ("first_name", "last_name", "email", "phone")
    filter_horizontal = ("service_areas",)


@admin.register(MarketplaceDriverProfile)
class MarketplaceDriverProfileAdmin(admin.ModelAdmin):
    list_display = ("display_name", "business_name", "verification_status", "is_published", "updated_at")
    list_filter = ("verification_status", "is_published", "accepts_quote_requests")
    search_fields = ("display_name", "business_name", "business_identifier", "user__email")
    filter_horizontal = ("airports", "service_areas")


@admin.register(DriverInquiry)
class DriverInquiryAdmin(admin.ModelAdmin):
    list_display = ("customer_name", "driver", "airport", "status", "created_at")
    list_filter = ("status", "airport")
    search_fields = ("customer_name", "customer_email", "customer_phone", "destination")
    readonly_fields = ("public_id", "created_at", "updated_at")


@admin.register(Vehicle)
class VehicleAdmin(admin.ModelAdmin):
    list_display = ("label", "registration", "seats", "luggage_capacity", "active")
    list_filter = ("active", "accessibility_capable")
    search_fields = ("label", "registration")


@admin.register(DriverAssignment)
class DriverAssignmentAdmin(admin.ModelAdmin):
    list_display = ("booking", "driver", "vehicle", "assigned_at", "unassigned_at")
    list_filter = ("unassigned_at",)
    search_fields = ("booking__reference", "driver__first_name", "driver__last_name", "vehicle__registration")
    readonly_fields = ("public_id", "assigned_at", "assigned_by", "unassigned_at", "unassigned_by")


@admin.register(AuditEvent)
class AuditEventAdmin(admin.ModelAdmin):
    list_display = ("action", "actor", "content_type", "object_id", "created_at")
    list_filter = ("action", "content_type")
    search_fields = ("object_id", "reason", "actor__email")
    readonly_fields = tuple(field.name for field in AuditEvent._meta.fields)

