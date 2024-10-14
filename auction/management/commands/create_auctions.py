import random
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.utils import timezone

from auction.factories import AuctionFactory, BidFactory
from auction.models import Category, Tag
from auction.models.auction import (
    AcceptedBiddersChoices,
    Auction,
    ConditionChoices,
    CurrencyChoices,
    StatusChoices,
)
from auction.models.category import CategoryChoices
from auction.models.tags import TagChoices
from bid.models.bid import StatusChoices as BidStatusChoices


class Command(BaseCommand):
    help = "Generate 201 auction records with 3 bids each, proper relationships, and update top_bid accordingly"

    def handle(self, *args, **kwargs):
        number_of_auctions = 201
        tags_per_auction = 3
        bids_per_auction = 3

        categories = [
            Category.objects.get_or_create(name=choice[0])[0]
            for choice in CategoryChoices.choices
        ]

        tags = [
            Tag.objects.get_or_create(name=choice[0])[0] for choice in TagChoices.choices
        ]

        for _ in range(number_of_auctions):
            condition = random.choice([choice[0] for choice in ConditionChoices.choices])
            status = random.choice(
                [
                    choice[0]
                    for choice in StatusChoices.choices
                    if choice[0] != StatusChoices.DELETED
                ]
            )
            accepted_bidders = random.choice(
                [choice[0] for choice in AcceptedBiddersChoices.choices]
            )
            currency = random.choice([choice[0] for choice in CurrencyChoices.choices])
            category = random.choice(categories)

            start_date = timezone.now() + timezone.timedelta(days=random.randint(1, 30))
            end_date = start_date + timezone.timedelta(days=random.randint(1, 7))

            auction = AuctionFactory(
                category=category,
                condition=condition,
                status=status,
                accepted_bidders=accepted_bidders,
                currency=currency,
                start_date=start_date,
                end_date=end_date,
            )

            random_tags = random.sample(tags, tags_per_auction)
            auction.tags.set(random_tags)

            approved_bids = []

            for _ in range(bids_per_auction):

                bid_status = random.choice(
                    [choice[0] for choice in BidStatusChoices.choices]
                )

                offer = Decimal(random.uniform(100, 5000)).quantize(Decimal("0.01"))
                description = f"Bid for auction {auction.auction_name}"
                delivery_fee = Decimal(random.uniform(10, 100)).quantize(Decimal("0.01"))

                bid = BidFactory(
                    auction=auction,
                    offer=offer,
                    description=description,
                    delivery_fee=delivery_fee,
                    status=bid_status,
                )

                if bid_status == BidStatusChoices.APPROVED:
                    approved_bids.append(bid)

            if approved_bids:
                top_bid_value = min(approved_bids, key=lambda x: x.offer).offer
                auction.top_bid = top_bid_value
                auction.save()

        auction_count = Auction.objects.count()
        self.stdout.write(
            self.style.SUCCESS(
                f"Successfully created {number_of_auctions} auctions, "
                f"each with {bids_per_auction} bids, and updated top_bid accordingly!"
            )
        )
        self.stdout.write(
            self.style.SUCCESS(
                f"Total number of auctions in the database: {auction_count}"
            )
        )
