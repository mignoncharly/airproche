from __future__ import annotations

from datetime import timedelta

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.db.models import Q
from django.utils import timezone

from apps.accounts.models import AccountToken
from apps.bookings.models import Booking, GuestAccessToken, IdempotencyRecord
from apps.notifications.models import ContactMessage, EmailNotification
from apps.operations.models import DriverInquiry


class Command(BaseCommand):
    help = "Dry-run or apply explicitly approved personal-data retention periods."

    def add_arguments(self, parser):
        parser.add_argument("--booking-days", type=int, required=True)
        parser.add_argument("--contact-days", type=int, required=True)
        parser.add_argument("--notification-days", type=int, required=True)
        parser.add_argument("--token-grace-days", type=int, default=7)
        parser.add_argument("--marketplace-inquiry-days", type=int, default=365)
        parser.add_argument("--marketplace-spam-days", type=int, default=30)
        parser.add_argument("--apply", action="store_true")

    def handle(self, *args, **options):
        periods = {
            "booking": options["booking_days"],
            "contact": options["contact_days"],
            "notification": options["notification_days"],
            "token_grace": options["token_grace_days"],
            "marketplace_inquiry": options["marketplace_inquiry_days"],
            "marketplace_spam": options["marketplace_spam_days"],
        }
        if any(value < 1 for value in periods.values()):
            raise CommandError("Retention periods must be positive whole days.")

        now = timezone.now()
        terminal = (Booking.Status.COMPLETED, Booking.Status.CANCELLED, Booking.Status.NO_SHOW)
        bookings = Booking.objects.filter(
            status__in=terminal,
            pickup_at__lt=now - timedelta(days=periods["booking"]),
        )
        contacts = ContactMessage.objects.filter(
            created_at__lt=now - timedelta(days=periods["contact"])
        )
        notifications = EmailNotification.objects.filter(
            created_at__lt=now - timedelta(days=periods["notification"])
        )
        token_cutoff = now - timedelta(days=periods["token_grace"])
        account_tokens = AccountToken.objects.filter(
            Q(expires_at__lt=token_cutoff) | Q(consumed_at__lt=token_cutoff)
        )
        guest_tokens = GuestAccessToken.objects.filter(
            Q(expires_at__lt=token_cutoff) | Q(revoked_at__lt=token_cutoff)
        )
        idempotency = IdempotencyRecord.objects.filter(expires_at__lt=now)
        marketplace_inquiries = DriverInquiry.objects.filter(
            status__in=(
                DriverInquiry.Status.DECLINED,
                DriverInquiry.Status.CLOSED,
                DriverInquiry.Status.ARCHIVED,
            ),
            updated_at__lt=now - timedelta(days=periods["marketplace_inquiry"]),
            anonymized_at__isnull=True,
        )
        marketplace_spam = DriverInquiry.objects.filter(
            status=DriverInquiry.Status.SPAM,
            updated_at__lt=now - timedelta(days=periods["marketplace_spam"]),
            anonymized_at__isnull=True,
        )

        counts = {
            "bookings_to_anonymize": bookings.count(),
            "contacts_to_delete": contacts.count(),
            "notifications_to_delete": notifications.count(),
            "account_tokens_to_delete": account_tokens.count(),
            "guest_tokens_to_delete": guest_tokens.count(),
            "idempotency_records_to_delete": idempotency.count(),
            "marketplace_inquiries_to_anonymize": marketplace_inquiries.count(),
            "marketplace_spam_to_anonymize": marketplace_spam.count(),
        }
        for key, value in counts.items():
            self.stdout.write(f"{key}={value}")
        if not options["apply"]:
            self.stdout.write(
                self.style.WARNING("Dry run only. Re-run with --apply after policy approval.")
            )
            return

        with transaction.atomic():
            for booking in bookings.select_for_update().iterator():
                self._anonymize_booking(booking)
            contacts.delete()
            notifications.delete()
            account_tokens.delete()
            guest_tokens.delete()
            idempotency.delete()
            for inquiry in (marketplace_inquiries | marketplace_spam).select_for_update().distinct():
                self._anonymize_marketplace_inquiry(inquiry)
        self.stdout.write(self.style.SUCCESS("Approved retention policy applied."))

    @staticmethod
    def _anonymize_booking(booking: Booking) -> None:
        marker = str(booking.public_id).replace("-", "")
        booking.customer = None
        booking.pickup_address = ""
        booking.destination_address = ""
        booking.pickup_locality = ""
        booking.destination_locality = ""
        booking.flight_number = ""
        booking.airline = ""
        booking.origin_city_country = ""
        booking.terminal = ""
        booking.meeting_information = ""
        booking.accessibility_details = ""
        booking.additional_requirements = ""
        booking.booker_first_name = "Anonymized"
        booking.booker_last_name = "Customer"
        booking.booker_email = f"anonymized+{marker}@example.invalid"
        booking.booker_phone = ""
        booking.booker_whatsapp = ""
        booking.passenger_first_name = "Anonymized"
        booking.passenger_last_name = "Passenger"
        booking.passenger_phone = ""
        booking.passenger_whatsapp = ""
        booking.cancellation_reason = ""
        booking.save(
            update_fields=(
                "customer",
                "pickup_address",
                "destination_address",
                "pickup_locality",
                "destination_locality",
                "flight_number",
                "airline",
                "origin_city_country",
                "terminal",
                "meeting_information",
                "accessibility_details",
                "additional_requirements",
                "booker_first_name",
                "booker_last_name",
                "booker_email",
                "booker_phone",
                "booker_whatsapp",
                "passenger_first_name",
                "passenger_last_name",
                "passenger_phone",
                "passenger_whatsapp",
                "cancellation_reason",
                "updated_at",
            )
        )
        booking.address_snapshots.update(
            formatted_address="",
            locality="",
            postal_code="",
            country_code="",
            latitude=None,
            longitude=None,
            provider_place_id="",
        )
        booking.contact_snapshots.update(
            first_name="Anonymized",
            last_name="",
            email="",
            phone="",
            whatsapp="",
        )
        booking.notes.all().delete()
        booking.status_history.update(note="")
        booking.guest_tokens.all().delete()
        booking.driver_assignments.update(override_reason="")

    @staticmethod
    def _anonymize_marketplace_inquiry(inquiry: DriverInquiry) -> None:
        marker = inquiry.public_id.hex
        inquiry.customer_name = "Client anonymisé"
        inquiry.customer_email = f"anonymized+{marker}@example.invalid"
        inquiry.customer_phone = ""
        inquiry.customer_whatsapp = ""
        inquiry.destination = ""
        inquiry.message = ""
        inquiry.source_fingerprint = ""
        inquiry.request_hash = ""
        inquiry.idempotency_key = ""
        inquiry.anonymized_at = timezone.now()
        inquiry.save(update_fields=(
            "customer_name", "customer_email", "customer_phone", "customer_whatsapp",
            "destination", "message", "source_fingerprint", "request_hash",
            "idempotency_key", "anonymized_at", "updated_at",
        ))
        inquiry.notes.all().delete()
        inquiry.status_history.update(note="", customer_visible_note="")
        EmailNotification.objects.filter(
            related_type="driver_inquiry", related_public_id=inquiry.public_id
        ).delete()
