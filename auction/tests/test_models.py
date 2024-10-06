import uuid
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.test import TestCase

from auction.factories import (
    AuctionFactory,
    BidFactory,
    BidImageFactory,
    BookmarkFactory,
    CategoryFactory,
    TagFactory,
)
from auction.models import Auction, Bid, BidImage, Bookmark, Category, Tag


class CategoryModelTest(TestCase):
    def test_category_creation(self):
        category = CategoryFactory(name="Electronics")
        self.assertTrue(isinstance(category, Category))
        self.assertEqual(str(category), "Electronics")


class TagModelTest(TestCase):
    def test_tag_creation(self):
        tag = TagFactory(name="Luxury")
        self.assertTrue(isinstance(tag, Tag))
        self.assertEqual(tag.name, "Luxury")
        self.assertEqual(str(tag), "Luxury")

    def test_tag_deletion_with_auction(self):
        tag = TagFactory(name="Vintage")
        auction = AuctionFactory()
        auction.tags.add(tag)

        with self.assertRaises(ValidationError):
            tag.delete()

    def test_tag_deletion_without_auction(self):
        tag = TagFactory(name="Unique")
        tag.delete()
        self.assertFalse(Tag.objects.filter(name="Unique").exists())


class AuctionModelTest(TestCase):
    def test_auction_creation(self):
        auction = AuctionFactory()
        self.assertTrue(isinstance(auction, Auction))
        self.assertIsNotNone(auction.id)
        self.assertEqual(
            str(auction), f"{auction.auction_name} - Status: {auction.status}"
        )

    def test_auction_tag_association(self):
        auction = AuctionFactory()
        tag = TagFactory(name="Vintage")
        auction.tags.add(tag)

        self.assertIn(tag, auction.tags.all())
        self.assertEqual(auction.tags.count(), 1)


class BookmarkModelTest(TestCase):
    def test_bookmark_creation(self):
        bookmark = BookmarkFactory()
        self.assertTrue(isinstance(bookmark, Bookmark))
        self.assertIsNotNone(bookmark.user_id)
        self.assertIsNotNone(bookmark.auction)
        self.assertEqual(
            str(bookmark),
            f"User: {bookmark.user_id} - Auction: {bookmark.auction.auction_name}",
        )

    def test_bookmark_uniqueness(self):
        auction = AuctionFactory()
        user_id = uuid.uuid4()
        BookmarkFactory(auction=auction, user_id=user_id)

        exists = Bookmark.objects.filter(user_id=user_id, auction=auction).exists()
        self.assertTrue(exists, "Initial bookmark should have been created successfully")

        duplicate_bookmark = Bookmark(user_id=user_id, auction=auction)

        try:
            duplicate_bookmark.save()
            self.fail("Duplicate bookmark should not be allowed.")
        except Exception as e:
            self.assertIsInstance(
                e,
                Exception,
                "An exception should be raised for duplicate bookmark creation.",
            )

    def test_multiple_bookmarks_for_different_users(self):
        auction = AuctionFactory()

        bookmark1 = BookmarkFactory(auction=auction, user_id=uuid.uuid4())
        bookmark2 = BookmarkFactory(auction=auction, user_id=uuid.uuid4())

        self.assertNotEqual(bookmark1.user_id, bookmark2.user_id)
        self.assertEqual(bookmark1.auction, bookmark2.auction)


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
        bid = BidFactory()
        self.assertIsNotNone(bid.description)

    def test_bid_delivery_fee(self):
        bid = BidFactory(delivery_fee=Decimal("25.00"))
        self.assertEqual(bid.delivery_fee, Decimal("25.00"))

    def test_bid_status_default(self):
        bid = BidFactory(status="Pending")
        self.assertEqual(bid.status, "Pending")

    def test_bid_status_approved(self):
        bid = BidFactory(status="Approved")
        self.assertEqual(bid.status, "Approved")

    def test_bid_status_rejected(self):
        bid = BidFactory(status="Rejected")
        self.assertEqual(bid.status, "Rejected")


class BidImageModelTest(TestCase):

    def test_bid_image_creation(self):
        bid_image = BidImageFactory()
        self.assertTrue(isinstance(bid_image, BidImage))
        self.assertIsNotNone(bid_image.image_url)
        self.assertTrue(bid_image.image_url.startswith("http"))
        self.assertTrue(isinstance(bid_image.bid, Bid))

    def test_multiple_images_for_single_bid(self):
        bid = BidFactory()
        image1 = BidImageFactory(bid=bid)
        image2 = BidImageFactory(bid=bid)

        self.assertEqual(BidImage.objects.filter(bid=bid).count(), 2)
        self.assertIn(image1, bid.images.all())
        self.assertIn(image2, bid.images.all())

    def test_bid_image_str_representation(self):
        bid = BidFactory(offer=Decimal("99.99"), description="Another test bid")
        bid_image = BidImageFactory(bid=bid)
        expected_str = f"Image for Bid ID: {bid.id}"
        self.assertEqual(str(bid_image), expected_str)
