import uuid

from django.db import models
from django_countries.fields import CountryField


class ConditionChoices(models.TextChoices):
    NEW = "New", "New"
    USED_LIKE_NEW = "Used - Like New", "Used - Like New"
    USED_VERY_GOOD = "Used - Very Good", "Used - Very Good"
    USED_GOOD = "Used - Good", "Used - Good"
    USED_ACCEPTABLE = "Used - Acceptable", "Used - Acceptable"


class StatusChoices(models.TextChoices):
    LIVE = "Live", "Live"
    DRAFT = "Draft", "Draft"
    COMPLETED = "Completed", "Completed"
    CANCELED = "Canceled", "Canceled"
    DELETED = "Deleted", "Deleted"


class AcceptedBiddersChoices(models.TextChoices):
    COMPANY = "Company", "Company"
    INDIVIDUAL = "Individual", "Individual"
    BOTH = "Both", "Both"


class CurrencyChoices(models.TextChoices):
    GEL = "GEL", "GEL"
    USD = "USD", "USD"
    EUR = "EUR", "EUR"


class AuctionManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().exclude(status=StatusChoices.DELETED)


class Auction(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    author = models.UUIDField()
    author_avatar = models.CharField(max_length=255, blank=True, null=True)
    author_nickname = models.CharField(max_length=255, blank=True, null=True)
    author_kyc_verified = models.BooleanField(default=False)
    auction_name = models.CharField(max_length=255)
    description = models.TextField()
    category = models.ForeignKey("Category", on_delete=models.PROTECT)
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    max_price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField(default=1)
    accepted_bidders = models.CharField(
        max_length=20,
        choices=AcceptedBiddersChoices.choices,
        default=AcceptedBiddersChoices.BOTH,
    )
    accepted_locations = CountryField(multiple=True, blank=True)
    tags = models.ManyToManyField("Tag", related_name="auctions")
    status = models.CharField(
        max_length=20, choices=StatusChoices.choices, default=StatusChoices.DRAFT
    )
    currency = models.CharField(
        max_length=3, choices=CurrencyChoices.choices, default=CurrencyChoices.GEL
    )
    custom_fields = models.JSONField(blank=True, null=True)
    condition = models.CharField(
        max_length=50, choices=ConditionChoices.choices, default=ConditionChoices.NEW
    )
    created_at = models.DateTimeField(
        auto_now_add=True, verbose_name="Auction Created At"
    )
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Auction Updated At")

    objects = AuctionManager()

    class Meta:
        ordering = [
            "-created_at",
        ]

    def __str__(self):
        return f"{self.auction_name} - Status: {self.status}"


class AuctionStatistics(models.Model):
    auction = models.OneToOneField(
        "Auction", on_delete=models.CASCADE, related_name="statistics"
    )

    # Winning bid details
    winner_bid = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True
    )
    winner_bid_author = models.UUIDField(null=True, blank=True)

    # Top bid details
    top_bid = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    top_bid_author = models.UUIDField(null=True, blank=True)

    # Viewing and bidding metrics
    views_count = models.PositiveIntegerField(default=0)
    total_bids_count = models.PositiveIntegerField(default=0)

    # Metric of how many users have bookmarked the auction
    bookmarks_count = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"Statistics for {self.auction.auction_name}"
