from django.db import models


class Bid(models.Model):
    offer = models.DecimalField(max_digits=20, decimal_places=2)
    description = models.TextField(
        blank=True, null=True, help_text="Enter a detailed description of the bid"
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
