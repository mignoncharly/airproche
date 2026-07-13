from __future__ import annotations

import json

from django.contrib.admin.models import ADDITION, CHANGE, DELETION, LogEntry
from django.contrib.contenttypes.models import ContentType
from rest_framework.permissions import DjangoModelPermissions
from rest_framework.viewsets import ModelViewSet


class StaffModelPermissions(DjangoModelPermissions):
    perms_map = {
        **DjangoModelPermissions.perms_map,
        "GET": ["%(app_label)s.view_%(model_name)s"],
        "OPTIONS": [],
        "HEAD": [],
    }

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_staff) and super().has_permission(
            request, view
        )


class AuditedStaffModelViewSet(ModelViewSet):
    permission_classes = (StaffModelPermissions,)

    def write_audit(self, instance, action_flag: int, message: dict):
        LogEntry.objects.create(
            user_id=self.request.user.pk,
            content_type=ContentType.objects.get_for_model(instance, for_concrete_model=False),
            object_id=str(instance.pk),
            object_repr=str(instance)[:200],
            action_flag=action_flag,
            change_message=json.dumps([message]),
        )

    def perform_create(self, serializer):
        instance = serializer.save()
        self.write_audit(
            instance,
            ADDITION,
            {"added": {"name": instance._meta.verbose_name, "object": str(instance)}},
        )

    def perform_update(self, serializer):
        instance = serializer.save()
        self.write_audit(
            instance,
            CHANGE,
            {"changed": {"fields": sorted(serializer.validated_data)}},
        )

    def perform_destroy(self, instance):
        self.write_audit(instance, DELETION, {"deleted": {"object": str(instance)}})
        instance.delete()
