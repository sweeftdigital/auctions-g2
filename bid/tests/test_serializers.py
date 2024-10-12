from unittest.mock import MagicMock
from uuid import uuid4

from rest_framework import serializers
from rest_framework.test import APITestCase

from auction.models import Auction, Category
from auction.models.auction import AcceptedBiddersChoices, StatusChoices
from bid.models import BidImage
from bid.serializers import BidSerializer


class MockUser:
    def __init__(
        self, user_id=None, is_seller=False, is_individual=False, is_company=False
    ):
        self.id = user_id or uuid4()
        self.is_authenticated = True
        self.is_seller = is_seller
        self._is_individual = is_individual
        self._is_company = is_company

    def is_individual(self):
        return self._is_individual

    def is_company(self):
        return self._is_company


class BidSerializerTests(APITestCase):

    def setUp(self):
        self.category = Category.objects.create(name="Electronics")

        self.user_seller = MockUser(user_id=uuid4(), is_seller=True, is_individual=True)
        self.user_non_seller = MockUser(
            user_id=uuid4(), is_seller=False, is_individual=True
        )
        self.user_seller_company = MockUser(
            user_id=uuid4(), is_seller=True, is_company=True
        )
        self.user_neither = MockUser(user_id=uuid4(), is_seller=True)

        self.auction = Auction.objects.create(
            author=self.user_seller.id,
            auction_name="Test Auction",
            description="Test Description",
            category=self.category,
            start_date="2024-10-01",
            end_date="2024-10-31",
            max_price=1000.00,
            quantity=1,
            status=StatusChoices.LIVE,  # Initially live
            accepted_bidders=AcceptedBiddersChoices.BOTH,
        )

    def test_auction_not_live(self):
        """Test that an error is raised when trying to bid on a non-live auction."""
        self.auction.status = StatusChoices.DRAFT
        context = {"request": MagicMock(user=self.user_seller), "auction": self.auction}
        data = {"offer": 500}

        serializer = BidSerializer(data=data, context=context)

        with self.assertRaises(serializers.ValidationError) as e:
            serializer.is_valid(raise_exception=True)

        self.assertIn(
            "You can only bid on live auctions.", e.exception.detail["non_field_errors"]
        )

    def test_user_not_seller(self):
        """Test that an error is raised when a non-seller user tries to bid."""
        context = {
            "request": MagicMock(user=self.user_non_seller),
            "auction": self.auction,
        }
        data = {"offer": 500}

        serializer = BidSerializer(data=data, context=context)

        with self.assertRaises(serializers.ValidationError) as e:
            serializer.is_valid(raise_exception=True)

        self.assertIn(
            "Only sellers can place bids.", e.exception.detail["non_field_errors"]
        )

    def test_only_companies_can_bid(self):
        """Test that only companies can bid on the auction when accepted_bidders is COMPANY."""
        self.auction.accepted_bidders = AcceptedBiddersChoices.COMPANY
        context = {"request": MagicMock(user=self.user_seller), "auction": self.auction}
        data = {"offer": 500}

        serializer = BidSerializer(data=data, context=context)

        with self.assertRaises(serializers.ValidationError) as e:
            serializer.is_valid(raise_exception=True)

        self.assertIn(
            "Only companies can bid on this auction.",
            e.exception.detail["non_field_errors"],
        )

    def test_only_individuals_can_bid(self):
        """Test that only individuals can bid on the auction when accepted_bidders is INDIVIDUAL."""
        self.auction.accepted_bidders = AcceptedBiddersChoices.INDIVIDUAL
        context = {
            "request": MagicMock(user=self.user_seller_company),
            "auction": self.auction,
        }
        data = {"offer": 500}

        serializer = BidSerializer(data=data, context=context)

        with self.assertRaises(serializers.ValidationError) as e:
            serializer.is_valid(raise_exception=True)

        self.assertIn(
            "Only individuals can bid on this auction.",
            e.exception.detail["non_field_errors"],
        )

    def test_both_individuals_and_companies_can_bid(self):
        """Test that only individuals or companies can bid when accepted_bidders is BOTH."""
        self.auction.accepted_bidders = AcceptedBiddersChoices.BOTH
        context = {"request": MagicMock(user=self.user_neither), "auction": self.auction}
        data = {"offer": 500}

        serializer = BidSerializer(data=data, context=context)

        with self.assertRaises(serializers.ValidationError) as e:
            serializer.is_valid(raise_exception=True)

        self.assertIn(
            "Only individuals or companies can bid on this auction.",
            e.exception.detail["non_field_errors"],
        )

    def test_bid_image_creation(self):
        """Test that BidImage objects are created when images are provided."""
        context = {"request": MagicMock(user=self.user_seller), "auction": self.auction}
        data = {
            "offer": 500,
            "description": "Test bid with images",
            "delivery_fee": 50,
            "images": [
                {"image_url": "http://example.com/image1.jpg"},
                {"image_url": "http://example.com/image2.jpg"},
            ],
        }

        serializer = BidSerializer(data=data, context=context)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        bid = serializer.save()

        self.assertEqual(BidImage.objects.filter(bid=bid).count(), 2)

        images = BidImage.objects.filter(bid=bid)
        self.assertEqual(images[0].image_url, "http://example.com/image1.jpg")
        self.assertEqual(images[1].image_url, "http://example.com/image2.jpg")
