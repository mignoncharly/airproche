from django.contrib import admin

from .models import Airport, ServiceArea


@admin.register(Airport)
class AirportAdmin(admin.ModelAdmin):
    list_display = ("name", "iata_code", "city", "country_code", "is_active", "display_order")
    list_editable = ("is_active", "display_order")
    list_filter = ("is_active", "country_code")
    search_fields = ("name", "iata_code", "city", "address")
    prepopulated_fields = {"slug": ("name",)}


@admin.register(ServiceArea)
class ServiceAreaAdmin(admin.ModelAdmin):
    list_display = ("name", "area_type", "city", "region", "is_active", "display_order")
    list_editable = ("is_active", "display_order")
    list_filter = ("is_active", "area_type", "country_code")
    search_fields = ("name", "city", "region")
    prepopulated_fields = {"slug": ("name",)}
