import uuid
from decimal import Decimal

from django.test import TestCase

from auction.factories import BidFactory, BidImageFactory
from bid.models import Bid, BidImage
from bid.models.bid import StatusChoices


class BidModelTest(TestCase):

    def test_bid_str_representation_exactly_50_chars(self):
        description = "This is a test bid description that is exactly fifty chars."
        bid = BidFactory(offer=Decimal("150.50"), description=description)

        expected_str = f"Bid of $150.50 - {description[:50]}"
        self.assertEqual(str(bid), expected_str)

    def test_bid_str_representation_truncated(self):
        description = (
            "This is a longer description for a test bid that exceeds fifty characters."
        )
        bid = BidFactory(offer=Decimal("150.50"), description=description)

        expected_str = f"Bid of $150.50 - {description[:50]}"
        self.assertEqual(str(bid), expected_str)

    def test_bid_default_description(self):
        """Testing that a bid is created with a non-empty description"""
        bid = BidFactory()
        self.assertIsNotNone(bid.description)
        self.assertNotEqual(
            bid.description.strip(), "", "Description should not be an empty string."
        )

    def test_bid_delivery_fee(self):
        """Ensures that delivery_fee is set correctly"""
        bid = BidFactory(delivery_fee=Decimal("25.00"))
        self.assertEqual(bid.delivery_fee, Decimal("25.00"))

    def test_bid_status_default(self):
        """Ensure the default status is 'Pending'"""
        bid = BidFactory()
        self.assertEqual(bid.status, StatusChoices.PENDING)

    def test_bid_status_approved(self):
        """Test that 'Approved' status can be assigned"""
        bid = BidFactory(status=StatusChoices.APPROVED)
        self.assertEqual(bid.status, StatusChoices.APPROVED)

    def test_bid_status_rejected(self):
        """Test that 'Rejected' status can be assigned"""
        bid = BidFactory(status=StatusChoices.REJECTED)
        self.assertEqual(bid.status, StatusChoices.REJECTED)

    def test_bid_author_field(self):
        """Ensure that an author UUID is set for each bid"""
        bid = BidFactory()
        self.assertIsNotNone(bid.author)
        self.assertIsInstance(bid.author, uuid.UUID)


class BidImageModelTest(TestCase):

    def test_bid_image_creation(self):
        """Test that a BidImage is correctly created and linked to a Bid"""
        bid_image = BidImageFactory()
        self.assertTrue(isinstance(bid_image, BidImage))
        self.assertIsNotNone(bid_image.image_url)
        self.assertTrue(bid_image.image_url.startswith("http"))
        self.assertTrue(isinstance(bid_image.bid, Bid))

    def test_multiple_images_for_single_bid(self):
        """Ensure multiple images can be associated with a single bid"""
        bid = BidFactory()
        image1 = BidImageFactory(bid=bid)
        image2 = BidImageFactory(bid=bid)

        self.assertEqual(BidImage.objects.filter(bid=bid).count(), 2)
        self.assertIn(image1, bid.images.all())
        self.assertIn(image2, bid.images.all())

    def test_bid_image_str_representation(self):
        """Test the string representation of a BidImage"""
        bid = BidFactory(offer=Decimal("99.99"), description="Another test bid")
        bid_image = BidImageFactory(bid=bid)
        expected_str = f"Image for Bid ID: {bid.id}"
        self.assertEqual(str(bid_image), expected_str)
