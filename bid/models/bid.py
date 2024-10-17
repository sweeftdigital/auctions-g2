import uuid

from django.db import models

from auction.models.auction import Auction


class StatusChoices(models.TextChoices):
    PENDING = "Pending", "Pending"
    APPROVED = "Approved", "Approved"
    REJECTED = "Rejected", "Rejected"


class Bid(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    author = models.UUIDField()
    auction = models.ForeignKey(
        Auction, related_name="bids", null=True, on_delete=models.CASCADE
    )
    offer = models.DecimalField(max_digits=20, decimal_places=2)
    description = models.TextField(
        blank=True, null=True, help_text="Enter a detailed description of the bid"
    )
    delivery_fee = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.00,
        help_text="Enter the delivery fee for the bid",
    )
    status = models.CharField(
        choices=StatusChoices.choices,
        default=StatusChoices.PENDING,
        max_length=20,
        help_text="Status of the bid",
    )

    def __str__(self):
        return f"Bid of ${self.offer} - {self.description[:50]}"


class BidImage(models.Model):
    bid = models.ForeignKey(Bid, on_delete=models.CASCADE, related_name="images")
    image_url = models.URLField(
        blank=True, null=True, help_text="URL of the uploaded image"
    )

    def __str__(self):
        return f"Image for Bid ID: {self.bid.id}"
