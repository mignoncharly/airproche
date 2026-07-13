from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import ContactMessageStaffViewSet, EmailNotificationStaffViewSet

router = DefaultRouter()
router.register("notifications", EmailNotificationStaffViewSet, basename="notification")
router.register("contacts", ContactMessageStaffViewSet, basename="contact")

notification_retry = EmailNotificationStaffViewSet.as_view({"post": "retry"})

urlpatterns = [
    path(
        "notifications/<uuid:public_id>/retry/",
        notification_retry,
        name="notification-retry",
    ),
    path("", include(router.urls)),
]
