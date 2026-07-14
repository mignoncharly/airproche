from django.apps import apps
from django.core.management.base import BaseCommand

from apps.content.legal_seed import publish, publish_airports


class Command(BaseCommand):
    help = "Idempotently publish approved Airproche marketplace identity, airports, legal documents, and FAQs."

    def handle(self, *args, **options):
        publish(apps, None)
        publish_airports(apps)
        self.stdout.write(self.style.SUCCESS("Airproche marketplace content and airports published."))
