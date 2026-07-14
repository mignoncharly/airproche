from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("django-admin/", admin.site.urls),
    path("api/v1/", include("apps.core.urls")),
    path("api/v1/auth/", include("apps.accounts.urls")),
    path("api/v1/public/", include("apps.content.urls")),
    path("api/v1/public/locations/", include("apps.locations.urls")),
    path("api/v1/public/pricing/", include("apps.pricing.urls")),
    path("api/v1/marketplace/", include(("apps.operations.marketplace_urls", "marketplace"), namespace="marketplace")),
    path("api/v1/bookings/", include("apps.bookings.urls")),
    path("api/v1/payments/", include("apps.payments.urls")),
    path("api/v1/staff/", include(("apps.core.staff_urls", "staff"), namespace="staff")),
    path(
        "api/v1/staff/operations/",
        include(("apps.operations.urls", "operations"), namespace="operations"),
    ),
    path("api/v1/contact/", include("apps.notifications.public_urls")),
    path(
        "api/v1/staff/communications/",
        include(("apps.notifications.urls", "communications"), namespace="communications"),
    ),
]
