from django.core.management import call_command
from django.test import TestCase

from auction.models import Auction, Category, Tag
from auction.models.category import CategoryChoices
from auction.models.tags import TagChoices


class CreateAuctionsCommandTest(TestCase):

    def setUp(self):
        self.number_of_auctions = 201
        self.tags_per_auction = 3
        self.categories_count = len(CategoryChoices.choices)
        self.tags_count = len(TagChoices.choices)

    def test_create_auctions_command(self):
        call_command("create_auctions")

        self.assertEqual(
            Auction.objects.count(),
            self.number_of_auctions,
            f"Should create {self.number_of_auctions} auctions.",
        )

        self.assertEqual(
            Category.objects.count(),
            self.categories_count,
            f"Should create {self.categories_count} categories.",
        )

        self.assertEqual(
            Tag.objects.count(), self.tags_count, f"Should create {self.tags_count} tags."
        )

        for auction in Auction.objects.all():
            self.assertIsNotNone(
                auction.category, "Auction should have a category assigned."
            )

            self.assertEqual(
                auction.tags.count(),
                self.tags_per_auction,
                f"Auction should have {self.tags_per_auction} tags.",
            )
