from django.contrib import admin

from .models import (
    AddressSnapshot, Booking, BookingNote, BookingStatusHistory,
    CancellationPolicySnapshot, ContactSnapshot, GuestAccessToken,
    IdempotencyRecord, PriceLine, PriceSnapshot,
)


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ("reference", "pickup_at", "status", "booker_email", "total_amount", "currency")
    list_filter = ("status", "booking_type", "airport", "source")
    search_fields = ("reference", "booker_email", "booker_last_name", "flight_number")
    readonly_fields = ("public_id", "reference", "created_at", "updated_at")
    list_select_related = ("airport", "service_area", "customer")


for model in (AddressSnapshot, ContactSnapshot, PriceSnapshot, PriceLine, CancellationPolicySnapshot, BookingStatusHistory, BookingNote, GuestAccessToken, IdempotencyRecord):
    admin.site.register(model)
