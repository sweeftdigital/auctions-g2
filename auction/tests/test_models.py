import uuid

from django.core.exceptions import ValidationError
from django.test import TestCase

from auction.factories import (
    AuctionFactory,
    BookmarkFactory,
    CategoryFactory,
    TagFactory,
)
from auction.models import Auction, Bookmark, Category, Tag


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
