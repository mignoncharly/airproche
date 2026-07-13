import re
import time

from django.utils import timezone
from rest_framework import serializers

from apps.accounts.models import User

from .models import ContactMessage, EmailDeliveryAttempt, EmailNotification

CONTROL_CHARACTERS = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")


class ContactSubmissionSerializer(serializers.Serializer):
    first_name = serializers.CharField(max_length=100, trim_whitespace=True)
    last_name = serializers.CharField(max_length=100, trim_whitespace=True)
    email = serializers.EmailField(max_length=254)
    phone = serializers.CharField(max_length=32, required=False, allow_blank=True)
    topic = serializers.ChoiceField(choices=ContactMessage.Topic.choices)
    message = serializers.CharField(min_length=10, max_length=4000, trim_whitespace=True)
    website = serializers.CharField(required=False, allow_blank=True, max_length=200)
    form_started_at = serializers.IntegerField(min_value=1)

    def validate(self, attrs):
        for field in ("first_name", "last_name", "email", "phone"):
            value = attrs.get(field, "")
            if any(character in value for character in ("\r", "\n", "\x00")):
                raise serializers.ValidationError({field: "Caractères non autorisés."})
        if CONTROL_CHARACTERS.search(attrs["message"]):
            raise serializers.ValidationError({"message": "Caractères non autorisés."})
        elapsed = int(time.time() * 1000) - attrs["form_started_at"]
        if elapsed < 3000:
            raise serializers.ValidationError(
                {"form_started_at": "Le formulaire a été envoyé trop rapidement."}
            )
        if elapsed > 2 * 60 * 60 * 1000:
            raise serializers.ValidationError(
                {"form_started_at": "Le formulaire a expiré. Rechargez la page."}
            )
        return attrs


class EmailAttemptSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmailDeliveryAttempt
        fields = (
            "attempt_number",
            "status",
            "provider_response",
            "error_code",
            "error_message",
            "created_at",
        )


class EmailNotificationSerializer(serializers.ModelSerializer):
    attempts = EmailAttemptSerializer(many=True, read_only=True)

    class Meta:
        model = EmailNotification
        fields = (
            "public_id",
            "kind",
            "recipient_email",
            "status",
            "retryable",
            "related_type",
            "related_public_id",
            "sent_at",
            "last_attempt_at",
            "created_at",
            "attempts",
        )


class ContactMessageSerializer(serializers.ModelSerializer):
    assigned_to = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.filter(is_staff=True), allow_null=True, required=False
    )

    class Meta:
        model = ContactMessage
        fields = (
            "public_id",
            "first_name",
            "last_name",
            "email",
            "phone",
            "topic",
            "message",
            "status",
            "assigned_to",
            "staff_notes",
            "created_at",
            "updated_at",
            "resolved_at",
        )
        read_only_fields = (
            "public_id",
            "first_name",
            "last_name",
            "email",
            "phone",
            "topic",
            "message",
            "created_at",
            "updated_at",
            "resolved_at",
        )

    def update(self, instance, validated_data):
        previous_status = instance.status
        instance = super().update(instance, validated_data)
        if instance.status == ContactMessage.Status.RESOLVED and not instance.resolved_at:
            instance.resolved_at = timezone.now()
            instance.save(update_fields=("resolved_at",))
        elif (
            previous_status == ContactMessage.Status.RESOLVED
            and instance.status != ContactMessage.Status.RESOLVED
        ):
            instance.resolved_at = None
            instance.save(update_fields=("resolved_at",))
        return instance
