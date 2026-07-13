from __future__ import annotations

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from apps.accounts.models import User
from apps.bookings.models import Booking

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
