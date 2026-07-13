from django.urls import path

from .views import AirportDetailView, AirportListView, ServiceAreaDetailView, ServiceAreaListView

app_name = "locations"

urlpatterns = [
    path("airports/", AirportListView.as_view(), name="airport-list"),
    path("airports/<slug:slug>/", AirportDetailView.as_view(), name="airport-detail"),
    path("service-areas/", ServiceAreaListView.as_view(), name="service-area-list"),
    path("service-areas/<slug:slug>/", ServiceAreaDetailView.as_view(), name="service-area-detail"),
]
