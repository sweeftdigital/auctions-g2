import uuid

from django.core.files.storage import storages
from django.db import models

from auction.models.auction import Auction


def get_big_images_storage():
    return storages["bid_images"]


class StatusChoices(models.TextChoices):
    PENDING = "Pending", "Pending"
    APPROVED = "Approved", "Approved"
    REJECTED = "Rejected", "Rejected"
    DELETED = "Deleted", "Deleted"
    REVOKED = "Revoked", "Revoked"
    CANCELED = "Canceled", "Canceled"


class Bid(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    author = models.UUIDField()
    author_avatar = models.CharField(max_length=255, blank=True, null=True)
    author_nickname = models.CharField(max_length=255, blank=True, null=True)
    author_kyc_verified = models.BooleanField(default=False)
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
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Bid Created At")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Bid Updated At")

    class Meta:
        ordering = [
            "offer",
            "-updated_at",
            "-created_at",
        ]
        indexes = [
            models.Index(
                fields=["auction", "created_at", "id"], name="idx_bid_auction_created"
            ),
        ]

    def __str__(self):
        return f"Bid of ${self.offer} - {self.description[:50]}"


class BidImage(models.Model):
    bid = models.ForeignKey(Bid, on_delete=models.CASCADE, related_name="images")
    image_url = models.ImageField(
        storage=get_big_images_storage(),
        blank=True,
        null=True,
        verbose_name="Bid Image",
    )

    def __str__(self):
        return f"Image for Bid ID: {self.bid.id}"
