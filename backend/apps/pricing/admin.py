from django.contrib import admin

from .models import Quote, QuoteLine, Tariff, TariffOption


class TariffOptionInline(admin.TabularInline):
    model = TariffOption
    extra = 0


@admin.register(Tariff)
class TariffAdmin(admin.ModelAdmin):
    list_display = (
        "airport",
        "service_area",
        "trip_type",
        "base_amount",
        "currency",
        "valid_from",
        "valid_until",
        "is_active",
    )
    list_filter = ("is_active", "trip_type", "currency", "airport")
    search_fields = ("airport__name", "airport__iata_code", "service_area__name")
    autocomplete_fields = ("airport", "service_area")
    inlines = (TariffOptionInline,)


@admin.register(TariffOption)
class TariffOptionAdmin(admin.ModelAdmin):
    list_display = ("code", "label", "tariff", "amount", "currency", "is_active")
    list_filter = ("is_active", "pricing_method", "currency")
    search_fields = ("code", "label")
    autocomplete_fields = ("tariff",)


class QuoteLineInline(admin.TabularInline):
    model = QuoteLine
    extra = 0
    can_delete = False
    readonly_fields = ("code", "label", "quantity", "unit_amount", "total_amount")


@admin.register(Quote)
class QuoteAdmin(admin.ModelAdmin):
    list_display = (
        "public_id",
        "trip_type",
        "airport_iata_code",
        "service_area_name",
        "pickup_at",
        "total_amount",
        "currency",
        "status",
        "expires_at",
    )
    list_filter = ("status", "trip_type", "currency", "airport")
    search_fields = ("public_id", "airport_name", "service_area_name")
    readonly_fields = tuple(field.name for field in Quote._meta.fields)
    inlines = (QuoteLineInline,)

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False
