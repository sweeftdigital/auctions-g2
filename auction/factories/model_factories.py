import uuid

import factory
from django.utils import timezone

from auction.models import Bid, BidImage
from auction.models.auction import (
    AcceptedBiddersChoices,
    Auction,
    ConditionChoices,
    CurrencyChoices,
    StatusChoices,
)
from auction.models.bookmark import Bookmark
from auction.models.category import Category
from auction.models.tags import Tag


class CategoryFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Category

    name = factory.Iterator(
        ["Electronics", "Vehicles", "Collectibles & Art", "Furniture"]
    )


class TagFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Tag

    name = factory.Iterator(["Luxury", "Vintage", "Compact", "Eco-friendly"])


class AuctionFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Auction

    id = factory.LazyFunction(uuid.uuid4)
    author = factory.LazyFunction(uuid.uuid4)
    auction_name = factory.Faker("word")
    description = factory.Faker("sentence")
    category = factory.SubFactory(CategoryFactory)
    start_date = factory.LazyFunction(timezone.now)
    end_date = factory.LazyFunction(lambda: timezone.now() + timezone.timedelta(days=10))
    max_price = factory.Faker("pydecimal", left_digits=6, right_digits=2, positive=True)
    quantity = factory.Faker("random_int", min=1, max=100)
    accepted_bidders = factory.Iterator(
        AcceptedBiddersChoices.choices, getter=lambda x: x[0]
    )
    accepted_locations = factory.Faker("random_element", elements=["GE", "AL", "HR"])
    status = factory.Iterator(StatusChoices.choices, getter=lambda x: x[0])
    currency = factory.Iterator(CurrencyChoices.choices, getter=lambda x: x[0])
    condition = factory.Iterator(ConditionChoices.choices, getter=lambda x: x[0])


class BookmarkFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Bookmark

    user_id = factory.LazyFunction(uuid.uuid4)
    auction = factory.SubFactory(AuctionFactory)


class BidFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Bid

    offer = factory.Faker("pydecimal", left_digits=5, right_digits=2, positive=True)
    description = factory.Faker("sentence")
    delivery_fee = factory.Faker(
        "pydecimal", left_digits=3, right_digits=2, positive=True
    )
    status = factory.Iterator(["Pending", "Approved", "Rejected"])


class BidImageFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = BidImage

    bid = factory.SubFactory(BidFactory)
    image_url = factory.Faker("image_url")
