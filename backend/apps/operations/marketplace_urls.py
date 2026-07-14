from django.urls import path

from .marketplace_views import DriverDirectoryDetailView, DriverDirectoryView, DriverInquiryCreateView, MyDriverInquiryView, MyDriverProfileView

app_name = "marketplace"

urlpatterns = [
    path("drivers/", DriverDirectoryView.as_view(), name="driver-list"),
    path("drivers/<uuid:public_id>/", DriverDirectoryDetailView.as_view(), name="driver-detail"),
    path("inquiries/", DriverInquiryCreateView.as_view(), name="inquiry-create"),
    path("me/profile/", MyDriverProfileView.as_view(), name="my-profile"),
    path("me/inquiries/", MyDriverInquiryView.as_view(), name="my-inquiries"),
]
