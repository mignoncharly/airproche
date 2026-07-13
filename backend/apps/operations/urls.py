from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    AssignmentActionView, BookingAuditView, BookingNoteActionView,
    BookingTransitionActionView, OperationsBookingDetailView,
    OperationsBookingListView, OperationsSummaryView, DriverStaffViewSet,
    UnassignmentActionView, VehicleStaffViewSet,
)

app_name = "operations"
router = DefaultRouter()
router.register("drivers", DriverStaffViewSet, basename="driver")
router.register("vehicles", VehicleStaffViewSet, basename="vehicle")

urlpatterns = [
    path("summary/", OperationsSummaryView.as_view(), name="summary"),
    path("bookings/", OperationsBookingListView.as_view(), name="booking-list"),
    path("bookings/<uuid:public_id>/", OperationsBookingDetailView.as_view(), name="booking-detail"),
    path("bookings/<uuid:public_id>/transition/", BookingTransitionActionView.as_view(), name="booking-transition"),
    path("bookings/<uuid:public_id>/notes/", BookingNoteActionView.as_view(), name="booking-note"),
    path("bookings/<uuid:public_id>/audit/", BookingAuditView.as_view(), name="booking-audit"),
    path("bookings/<uuid:public_id>/assignment/", AssignmentActionView.as_view(), name="assignment"),
    path("assignments/<uuid:public_id>/unassign/", UnassignmentActionView.as_view(), name="unassignment"),
    path("", include(router.urls)),
]

