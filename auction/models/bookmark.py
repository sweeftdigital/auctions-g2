import uuid

from django.db import models

from auction.models import Auction


class Bookmark(models.Model):
    id = models.UUIDField(
        primary_key=True, default=uuid.uuid4, editable=False, verbose_name="ID"
    )
    user_id = models.UUIDField()
    auction = models.ForeignKey(Auction, on_delete=models.CASCADE)
    created_at = models.DateTimeField(
        auto_now_add=True, verbose_name="Bookmark Created At"
    )

    class Meta:
        ordering = [
            "-created_at",
        ]

    def __str__(self):
        return f"User: {self.user_id} - Auction: {self.auction.auction_name}"
