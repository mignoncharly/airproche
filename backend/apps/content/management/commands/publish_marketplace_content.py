from django.apps import apps
from django.core.management.base import BaseCommand

from apps.content.legal_seed import publish


class Command(BaseCommand):
    help = "Idempotently publish approved Airproche marketplace identity, legal documents, and FAQs."

    def handle(self, *args, **options):
        publish(apps, None)
        self.stdout.write(self.style.SUCCESS("Airproche marketplace legal content published."))
