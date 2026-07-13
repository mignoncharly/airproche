from django.urls import path

from .dashboard import BookingReceiptView, CustomerBookingListView
from .repeat import RepeatBookingView
from .views import (
    BookingCancelView, BookingCreateView, BookingDetailView,
    BookingGuestAccessView, BookingTransitionView, MyBookingsView,
)

app_name = "bookings"

urlpatterns = [
    path("", BookingCreateView.as_view(), name="create"),
    path("mine/", CustomerBookingListView.as_view(), name="mine"),
    path("guest-access/", BookingGuestAccessView.as_view(), name="guest-access"),
    path("<uuid:public_id>/repeat/", RepeatBookingView.as_view(), name="repeat"),
    path("<uuid:public_id>/receipt/", BookingReceiptView.as_view(), name="receipt"),
    path("<uuid:public_id>/", BookingDetailView.as_view(), name="detail"),
    path("<uuid:public_id>/cancel/", BookingCancelView.as_view(), name="cancel"),
    path("<uuid:public_id>/transition/", BookingTransitionView.as_view(), name="transition"),
]
