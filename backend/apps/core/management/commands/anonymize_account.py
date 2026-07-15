from __future__ import annotations

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from apps.accounts.models import User
from apps.bookings.models import Booking
from apps.operations.models import MarketplaceDriverProfile

from .enforce_data_retention import Command as RetentionCommand


class Command(BaseCommand):
    help = "Dry-run or apply anonymization for one approved account erasure request."

    def add_arguments(self, parser):
        parser.add_argument("--public-id", required=True)
        parser.add_argument("--apply", action="store_true")

    def handle(self, *args, **options):
        try:
            user = User.objects.get(public_id=options["public_id"])
        except (User.DoesNotExist, ValueError) as exc:
            raise CommandError("Account not found.") from exc
        if user.is_staff or user.is_superuser:
            raise CommandError("Staff accounts require a separate access-review process.")

        terminal = (Booking.Status.COMPLETED, Booking.Status.CANCELLED, Booking.Status.NO_SHOW)
        nonterminal = user.bookings.exclude(status__in=terminal)
        if nonterminal.exists():
            raise CommandError("Account has nonterminal bookings and cannot be anonymized.")
        self.stdout.write(f"account={user.public_id}")
        self.stdout.write(f"terminal_bookings_to_anonymize={user.bookings.count()}")
        if not options["apply"]:
            self.stdout.write(
                self.style.WARNING("Dry run only. Re-run with --apply after request approval.")
            )
            return

        with transaction.atomic():
            locked = User.objects.select_for_update().get(pk=user.pk)
            for booking in locked.bookings.select_for_update().iterator():
                RetentionCommand._anonymize_booking(booking)
            profile = MarketplaceDriverProfile.objects.filter(user=locked).first()
            if profile:
                for inquiry in profile.inquiries.select_for_update().iterator():
                    RetentionCommand._anonymize_marketplace_inquiry(inquiry)
                profile.first_name = "Anonymized"
                profile.last_name = "Driver"
                profile.display_name = "Profil archivé"
                profile.business_name = ""
                profile.business_identifier = ""
                profile.professional_status = ""
                profile.vtc_card_number = ""
                profile.vtc_issuing_authority = ""
                profile.insurance_provider = ""
                profile.insurance_policy_reference = ""
                profile.bio = ""
                profile.professional_email = ""
                profile.phone = ""
                profile.whatsapp_phone = ""
                profile.profile_photo.delete(save=False)
                profile.is_published = False
                profile.verification_status = MarketplaceDriverProfile.VerificationStatus.ARCHIVED
                profile.status_reason = "Account anonymization"
                profile.verification_documents.all().delete()
                profile.verification_events.update(reason="", safe_metadata={})
                profile.save()
            marker = str(locked.public_id).replace("-", "")
            locked.email = f"anonymized+{marker}@example.invalid"
            locked.first_name = "Anonymized"
            locked.last_name = "Account"
            locked.phone = ""
            locked.email_verified_at = None
            locked.is_active = False
            locked.set_unusable_password()
            locked.save(
                update_fields=(
                    "email",
                    "first_name",
                    "last_name",
                    "phone",
                    "email_verified_at",
                    "is_active",
                    "password",
                )
            )
            locked.account_tokens.all().delete()
        self.stdout.write(self.style.SUCCESS("Approved account anonymization applied."))
