from django.urls import path

from .marketplace_views import (
    DriverDirectoryDetailView,
    DriverDirectoryView,
    DriverInquiryCreateView,
    DriverOnboardingOptionsView,
    MyDriverInquiryDetailView,
    MyDriverInquiryListView,
    MyDriverInquiryNoteView,
    MyDriverInquiryTransitionView,
    MyDriverProfileView,
)

app_name = "marketplace"

urlpatterns = [
    path("drivers/", DriverDirectoryView.as_view(), name="driver-list"),
    path("drivers/<str:identifier>/", DriverDirectoryDetailView.as_view(), name="driver-detail"),
    path("inquiries/", DriverInquiryCreateView.as_view(), name="inquiry-create"),
    path("me/profile/", MyDriverProfileView.as_view(), name="my-profile"),
    path("me/options/", DriverOnboardingOptionsView.as_view(), name="my-options"),
    path("me/inquiries/", MyDriverInquiryListView.as_view(), name="my-inquiries"),
    path(
        "me/inquiries/<uuid:public_id>/",
        MyDriverInquiryDetailView.as_view(),
        name="my-inquiry-detail",
    ),
    path(
        "me/inquiries/<uuid:public_id>/transition/",
        MyDriverInquiryTransitionView.as_view(),
        name="my-inquiry-transition",
    ),
    path(
        "me/inquiries/<uuid:public_id>/notes/",
        MyDriverInquiryNoteView.as_view(),
        name="my-inquiry-note",
    ),
]
