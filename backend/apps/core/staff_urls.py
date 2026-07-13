from rest_framework.routers import DefaultRouter

from apps.locations.staff import AirportStaffViewSet, ServiceAreaStaffViewSet
from apps.pricing.staff import TariffOptionStaffViewSet, TariffStaffViewSet

router = DefaultRouter()
router.register("airports", AirportStaffViewSet, basename="airport")
router.register("service-areas", ServiceAreaStaffViewSet, basename="service-area")
router.register("tariffs", TariffStaffViewSet, basename="tariff")
router.register("tariff-options", TariffOptionStaffViewSet, basename="tariff-option")

urlpatterns = router.urls
