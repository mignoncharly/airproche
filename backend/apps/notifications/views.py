from django.contrib.admin.models import CHANGE, LogEntry
from django.contrib.contenttypes.models import ContentType
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_protect
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet, ReadOnlyModelViewSet

from apps.core.staff import StaffModelPermissions

from .models import ContactMessage, EmailNotification
from .permissions import CommunicationPermission
from .serializers import (
    ContactMessageSerializer,
    ContactSubmissionSerializer,
    EmailNotificationSerializer,
)
from .services import create_contact_message, retry_notification


@method_decorator(csrf_protect, name="dispatch")
class ContactSubmissionView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]
    throttle_scope = "contact_submit"

    def post(self, request):
        serializer = ContactSubmissionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        if serializer.validated_data.get("website"):
            return Response(
                {"message": "Votre message a été reçu.", "idempotent_replay": False},
                status=status.HTTP_202_ACCEPTED,
            )
        message, duplicate = create_contact_message(
            serializer.validated_data,
            idempotency_key=request.headers.get("Idempotency-Key", ""),
            remote_addr=request.META.get("REMOTE_ADDR", ""),
        )
        return Response(
            {
                "public_id": message.public_id,
                "message": "Votre message a été reçu.",
                "idempotent_replay": duplicate,
            },
            status=status.HTTP_200_OK if duplicate else status.HTTP_201_CREATED,
        )


class EmailNotificationStaffViewSet(ReadOnlyModelViewSet):
    queryset = EmailNotification.objects.prefetch_related("attempts")
    serializer_class = EmailNotificationSerializer
    lookup_field = "public_id"
    permission_classes = (CommunicationPermission,)
    throttle_scope = "notification_read"

    @method_decorator(csrf_protect)
    def retry(self, request, public_id=None):
        notification = self.get_object()
        attempt = retry_notification(
            notification,
            idempotency_key=request.headers.get("Idempotency-Key", ""),
        )
        notification.refresh_from_db()
        return Response(
            {
                "notification": EmailNotificationSerializer(notification).data,
                "attempt_number": attempt.attempt_number,
                "attempt_status": attempt.status,
            }
        )


class ContactMessageStaffViewSet(ModelViewSet):
    queryset = ContactMessage.objects.select_related("assigned_to")
    serializer_class = ContactMessageSerializer
    lookup_field = "public_id"
    permission_classes = (StaffModelPermissions,)
    http_method_names = ("get", "patch", "head", "options")
    throttle_scope = "notification_read"

    def perform_update(self, serializer):
        instance = serializer.save()
        LogEntry.objects.create(
            user_id=self.request.user.pk,
            content_type=ContentType.objects.get_for_model(instance),
            object_id=str(instance.pk),
            object_repr=str(instance)[:200],
            action_flag=CHANGE,
            change_message='[{"changed":{"fields":["status","assigned_to","staff_notes"]}}]',
        )
