from django.core.management.base import BaseCommand

from auctions.rabbitmq.consumers import event_subscriber


class Command(BaseCommand):

    def handle(self, *args, **options):
        event_subscriber.start()
