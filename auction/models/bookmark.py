from django.db import models

from auction.models import Auction


class Bookmark(models.Model):
    user_id = models.UUIDField()
    auction = models.ForeignKey(Auction, on_delete=models.CASCADE)

    def __str__(self):
        return f"User: {self.user_id} - Auction: {self.auction.auction_name}"
