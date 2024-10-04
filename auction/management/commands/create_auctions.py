import random

from django.core.management.base import BaseCommand

from auction.factories import AuctionFactory
from auction.models import Category, Tag
from auction.models.auction import (
    AcceptedBiddersChoices,
    ConditionChoices,
    CurrencyChoices,
    StatusChoices,
)
from auction.models.category import CategoryChoices
from auction.models.tags import TagChoices


class Command(BaseCommand):
    help = "Generate 201 auction records with proper relationships and randomized choices for testing"

    def handle(self, *args, **kwargs):
        number_of_auctions = 201
        tags_per_auction = 3

        self.stdout.write(self.style.NOTICE("Creating or getting Categories and Tags..."))

        categories = [
            Category.objects.get_or_create(name=choice[0])[0]
            for choice in CategoryChoices.choices
        ]

        tags = [
            Tag.objects.get_or_create(name=choice[0])[0] for choice in TagChoices.choices
        ]

        self.stdout.write(self.style.NOTICE(f"Creating {number_of_auctions} auctions..."))

        for _ in range(number_of_auctions):
            condition = random.choice([choice[0] for choice in ConditionChoices.choices])
            status = random.choice([choice[0] for choice in StatusChoices.choices])
            accepted_bidders = random.choice(
                [choice[0] for choice in AcceptedBiddersChoices.choices]
            )
            currency = random.choice([choice[0] for choice in CurrencyChoices.choices])
            category = random.choice(categories)

            auction = AuctionFactory(
                category=category,
                condition=condition,
                status=status,
                accepted_bidders=accepted_bidders,
                currency=currency,
            )

            random_tags = random.sample(tags, tags_per_auction)
            auction.tags.set(random_tags)

        self.stdout.write(
            self.style.SUCCESS(
                f"Successfully created "
                f"{number_of_auctions} auctions with relationships and random choices!"
            )
        )
