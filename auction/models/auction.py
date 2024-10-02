import uuid

from django.db import models
from django_countries.fields import CountryField


class ConditionChoices(models.TextChoices):
    NEW = "New", "New"
    OPEN_BOX = "Open box", "Open box"
    EXCELLENT = "Excellent", "Excellent"
    VERY_GOOD = "Very Good", "Very Good"
    GOOD = "Good", "Good"
    USED = "Used", "Used"
    FOR_PARTS = "For parts or not working", "For parts or not working"


class StatusChoices(models.TextChoices):
    ACTIVE = "active", "Active"
    DRAFT = "draft", "Draft"
    COMPLETED = "completed", "Completed"
    CANCELED = "canceled", "Canceled"


class AcceptedBiddersChoices(models.TextChoices):
    COMPANY = "Company", "Company"
    INDIVIDUAL = "Individual", "Individual"
    BOTH = "Both", "Both"


class CurrencyChoices(models.TextChoices):
    GEL = "GEL", "GEL"
    USD = "USD", "USD"
    EUR = "EUR", "EUR"


class Auction(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    author = models.UUIDField()
    auction_name = models.CharField(max_length=255)
    description = models.TextField()
    category = models.ForeignKey("Category", on_delete=models.PROTECT)
    start_date = models.DateField()
    end_date = models.DateField()
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
    winner = models.UUIDField(null=True, blank=True)
    winner_bid_amount = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True
    )
    top_bid = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    condition = models.CharField(
        max_length=50, choices=ConditionChoices.choices, default=ConditionChoices.NEW
    )
    created_at = models.DateTimeField(
        auto_now_add=True, verbose_name="Auction Created At"
    )
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Auction Updated At")

    class Meta:
        ordering = [
            "-created_at",
        ]

    def __str__(self):
        return f"{self.auction_name} - Status: {self.status}"
