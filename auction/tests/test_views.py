from datetime import date, datetime, timedelta
from unittest.mock import patch
from uuid import uuid4

from django.db import IntegrityError
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient, APITestCase

from auction.authentication.user_proxy import UserProxy
from auction.factories.model_factories import (
    AuctionFactory,
    BookmarkFactory,
    CategoryFactory,
    TagFactory,
)
from auction.models import Auction, AuctionStatistics, Bookmark, Category
from auction.models.auction import (
    AcceptedBiddersChoices,
    ConditionChoices,
    StatusChoices,
)
from auction.views import BaseAuctionView, CreateDraftAuctionView, CreateLiveAuctionView
from bid.models import Bid


class MockUser:
    def __init__(self, user_id):
        self.id = user_id
        self.is_authenticated = True
        self.is_seller = False
        self.is_buyer = False
        self.country = "Georgia"
        self.avatar = "https://api.dicebear.com/9.x/micah/svg?seed=826"
        self.nickname = "SadWozniak777"


class BuyerAuctionListViewTests(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = MockUser(user_id=uuid4())
        self.client.force_authenticate(user=self.user)
        self.url = reverse("auction-list-buyer")

        self.category1 = CategoryFactory(name="Pet Supplies")
        self.category2 = CategoryFactory(name="Electronics")
        self.tag1 = TagFactory(name="Animals")
        self.tag2 = TagFactory(name="Water Device")

        self.auction1 = AuctionFactory(
            author=self.user.id,
            category=self.category1,
            status=StatusChoices.LIVE,
            accepted_bidders=AcceptedBiddersChoices.BOTH,
            accepted_locations="AL",
            start_date=timezone.now() - timedelta(days=5),
            end_date=timezone.now() + timedelta(days=2),
            max_price=100,
            quantity=1,
            auction_name="Awesome Pet Supplies Auction",
            description="Bid on the best pet supplies.",
        )
        self.auction1.tags.add(self.tag1, self.tag2)

        self.auction2 = AuctionFactory(
            author=self.user.id,
            category=self.category2,
            status=StatusChoices.LIVE,
            accepted_bidders=AcceptedBiddersChoices.COMPANY,
            accepted_locations="HR",
            start_date=timezone.now() - timedelta(days=2),
            end_date=timezone.now() + timedelta(days=1),
            max_price=200,
            quantity=2,
            auction_name="Old Electronics Auction",
            description="Bidding for various old electronics.",
        )
        self.auction2.tags.add(self.tag1)

        self.auction3 = AuctionFactory(
            author=uuid4(),
            category=self.category1,
            status=StatusChoices.LIVE,
            accepted_bidders=AcceptedBiddersChoices.COMPANY,
            accepted_locations="HR",
            start_date=timezone.now() - timedelta(days=2),
            end_date=timezone.now() + timedelta(days=1),
            max_price=300,
            quantity=3,
            auction_name="Auction from different user.",
            description="Simple auction.",
        )
        self.auction3.tags.add(self.tag1)

    def test_auction_listing(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data.get("results")), 2)
        self.assertIsNotNone(response.data["results"][0]["tags"])
        self.assertIsNotNone(response.data["results"][1]["tags"])

    def test_unauthenticated_access(self):
        self.client.logout()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_filter_by_status(self):
        response = self.client.get(self.url, {"status": StatusChoices.LIVE})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data.get("results")), 2)
        self.assertEqual(
            response.data["results"][0]["product"], self.auction2.auction_name
        )
        self.assertEqual(
            response.data["results"][1]["product"], self.auction1.auction_name
        )

    def test_filter_by_live_status(self):
        self.auction2.status = StatusChoices.COMPLETED
        self.auction2.save()
        response = self.client.get(self.url, {"status": StatusChoices.LIVE})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data.get("results")), 1)
        self.assertEqual(
            response.data["results"][0]["product"], self.auction1.auction_name
        )

    def test_filter_by_upcoming_status(self):
        self.auction1.start_date = timezone.now() + timedelta(days=1)
        self.auction1.end_date = timezone.now() + timedelta(days=2)
        self.auction1.save()
        response = self.client.get(self.url, {"status": "Upcoming"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data.get("results")), 1)
        self.assertEqual(
            response.data["results"][0]["product"], self.auction1.auction_name
        )

    def test_filter_by_status_other_than_live_or_upcoming(self):
        self.auction1.status = StatusChoices.COMPLETED
        self.auction1.save()
        response = self.client.get(self.url, {"status": self.auction1.status})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data.get("results")), 1)
        self.assertEqual(
            response.data["results"][0]["product"], self.auction1.auction_name
        )

    def test_filter_by_invalid_status(self):
        response = self.client.get(self.url, {"status": "invalid_status"})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_search_by_auction_name(self):
        response = self.client.get(self.url, {"search": "Awesome Pet Supplies Auction"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data.get("results")), 1)
        self.assertEqual(
            response.data["results"][0]["product"], self.auction1.auction_name
        )

    def test_search_by_description(self):
        response = self.client.get(
            self.url, {"search": "Bidding for various old electronics."}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data.get("results")), 1)
        self.assertEqual(
            response.data["results"][0]["product"], self.auction2.auction_name
        )

    def test_search_by_partial_match(self):
        response = self.client.get(self.url, {"search": "Awesome"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data.get("results")), 1)
        self.assertEqual(
            response.data["results"][0]["product"], self.auction1.auction_name
        )

    def test_search_by_no_results(self):
        response = self.client.get(self.url, {"search": "Nonexistent Auction"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data.get("results")), 0)

    def test_search_by_tags(self):
        response = self.client.get(self.url, {"search": "Animals"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data.get("results")), 2)
        self.assertEqual(
            response.data["results"][0]["product"], self.auction2.auction_name
        )

    def test_search_by_nonexistent_tag(self):
        response = self.client.get(self.url, {"search": "Nonexistent Tag"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data.get("results")), 0)

    def test_order_by_start_date_ascending(self):
        response = self.client.get(self.url + "?ordering=start_date")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data.get("results")), 2)
        self.assertEqual(
            response.data["results"][0]["product"], self.auction1.auction_name
        )

    def test_order_by_start_date_descending(self):
        response = self.client.get(self.url + "?ordering=-start_date")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data.get("results")), 2)
        self.assertEqual(
            response.data["results"][0]["product"], self.auction2.auction_name
        )

    def test_order_by_end_date_ascending(self):
        response = self.client.get(self.url + "?ordering=end_date")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data.get("results")), 2)
        self.assertEqual(
            response.data["results"][0]["product"], self.auction2.auction_name
        )

    def test_order_by_end_date_descending(self):
        response = self.client.get(self.url + "?ordering=-end_date")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data.get("results")), 2)
        self.assertEqual(
            response.data["results"][0]["product"], self.auction1.auction_name
        )

    def test_order_by_max_price_ascending(self):
        response = self.client.get(self.url + "?ordering=max_price")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data.get("results")), 2)
        self.assertEqual(
            response.data["results"][0]["product"], self.auction1.auction_name
        )

    def test_order_by_max_price_descending(self):
        response = self.client.get(self.url + "?ordering=-max_price")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data.get("results")), 2)
        self.assertEqual(
            response.data["results"][0]["product"], self.auction2.auction_name
        )

    def test_order_by_quantity_ascending(self):
        response = self.client.get(self.url + "?ordering=quantity")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data.get("results")), 2)
        self.assertEqual(
            response.data["results"][0]["product"], self.auction1.auction_name
        )

    def test_order_by_quantity_descending(self):
        response = self.client.get(self.url + "?ordering=-quantity")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data.get("results")), 2)
        self.assertEqual(
            response.data["results"][0]["product"], self.auction2.auction_name
        )

    def test_order_by_category_ascending(self):
        response = self.client.get(self.url + "?ordering=category")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data.get("results")), 2)
        self.assertEqual(
            response.data["results"][0]["product"], self.auction2.auction_name
        )

    def test_order_by_category_descending(self):
        response = self.client.get(self.url + "?ordering=-category")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data.get("results")), 2)
        self.assertEqual(response.data["results"][0]["category"], "Pet Supplies")
        self.assertEqual(response.data["results"][1]["category"], "Electronics")

    def test_auction_list_returns_only_auctions_of_author(self):
        # Check that the view does not return auctions of different users.
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data.get("results")), 2)
        self.assertNotEqual(
            response.data["results"][0]["product"], self.auction3.auction_name
        )
        self.assertNotEqual(
            response.data["results"][1]["product"], self.auction3.auction_name
        )

    def test_seller_trying_to_list_buyer_auctions(self):
        self.user.is_seller = True
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_auction_with_start_date_in_future(self):
        self.auction2.start_date = timezone.now() + timedelta(days=1)
        self.auction2.end_date = timezone.now() + timedelta(days=2)
        self.auction2.save()

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data.get("results")), 2)
        self.assertEqual(
            response.data["results"][0]["product"], self.auction2.auction_name
        )
        self.assertEqual(
            response.data["results"][1]["product"], self.auction1.auction_name
        )
        self.assertEqual(response.data["results"][0]["status"], "Upcoming")
        self.assertEqual(response.data["results"][1]["status"], StatusChoices.LIVE)

    def test_auction_with_deleted_status(self):
        self.auction2.status = StatusChoices.DELETED
        self.auction2.save()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data.get("results")), 1)
        self.assertEqual(response.data["results"][0]["status"], StatusChoices.LIVE)
        self.assertEqual(
            response.data["results"][0]["product"], self.auction1.auction_name
        )


class BuyerDashboardListViewTests(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = MockUser(user_id=uuid4())
        self.client.force_authenticate(user=self.user)
        self.url = reverse("buyer-dashboard")

        self.category1 = CategoryFactory(name="Pet Supplies")
        self.category2 = CategoryFactory(name="Electronics")
        self.tag1 = TagFactory(name="Animals")
        self.tag2 = TagFactory(name="Water Device")

        self.auction1 = AuctionFactory(
            author=self.user.id,
            category=self.category1,
            status=StatusChoices.LIVE,
            accepted_bidders=AcceptedBiddersChoices.BOTH,
            accepted_locations="AL",
            start_date=timezone.now() - timedelta(days=5),
            end_date=timezone.now() + timedelta(days=1),
            max_price=100,
            quantity=1,
            auction_name="Awesome Pet Supplies Auction",
            description="Bid on the best pet supplies.",
        )
        self.auction1.tags.add(self.tag1, self.tag2)

        self.auction2 = AuctionFactory(
            author=self.user.id,
            category=self.category2,
            status=StatusChoices.LIVE,
            accepted_bidders=AcceptedBiddersChoices.COMPANY,
            accepted_locations="HR",
            start_date=timezone.now() - timedelta(days=2),
            end_date=timezone.now() + timedelta(days=1),
            max_price=200,
            quantity=2,
            auction_name="Old Electronics Auction",
            description="Bidding for various old electronics.",
        )
        self.auction2.tags.add(self.tag1)

        self.auction3 = AuctionFactory(
            author=uuid4(),
            category=self.category1,
            status=StatusChoices.LIVE,
            accepted_bidders=AcceptedBiddersChoices.COMPANY,
            accepted_locations="HR",
            start_date=timezone.now() - timedelta(days=2),
            end_date=timezone.now() + timedelta(days=1),
            max_price=300,
            quantity=3,
            auction_name="Auction from different user.",
            description="Simple auction.",
        )
        self.auction3.tags.add(self.tag1)

    def test_dashboard_list_success(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data.get("results")), 2)
        self.assertEqual(response.data["results"][0]["author"], str(self.user.id))
        self.assertEqual(response.data["results"][1]["author"], str(self.user.id))

    def test_dashboard_list_upcoming_auctions(self):
        self.auction2.start_date = timezone.now() + timedelta(days=1)
        self.auction2.end_date = timezone.now() + timedelta(days=2)
        self.auction2.save()
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data.get("results")), 2)
        self.assertEqual(response.data["results"][0]["status"], "Upcoming")
        self.assertEqual(response.data["results"][1]["status"], "Live")


class SellerAuctionListViewTests(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = MockUser(user_id=uuid4())
        self.client.force_authenticate(user=self.user)
        self.url = reverse("auction-list-seller")

        self.category1 = CategoryFactory(name="Collectibles & Art")
        self.category2 = CategoryFactory(name="Automobiles")
        self.tag1 = TagFactory(name="Expensive")
        self.tag2 = TagFactory(name="Rare")

        self.auction1 = AuctionFactory(
            author=self.user.id,
            category=self.category1,
            status=StatusChoices.LIVE,
            accepted_bidders=AcceptedBiddersChoices.BOTH,
            start_date=timezone.now() - timedelta(days=1),
            end_date=timezone.now() + timedelta(days=1),
            max_price=5000,
            quantity=1,
            auction_name="Exclusive Art Auction",
            description="Rare and expensive art pieces.",
        )
        self.auction1.tags.add(self.tag1)

        self.auction2 = AuctionFactory(
            author=uuid4(),
            category=self.category2,
            status=StatusChoices.LIVE,
            accepted_bidders=AcceptedBiddersChoices.BOTH,
            start_date=timezone.now() + timedelta(days=1),
            end_date=timezone.now() + timedelta(days=5),
            max_price=20000,
            quantity=2,
            auction_name="Luxury Car Auction",
            description="Luxury cars for bidding.",
        )
        self.auction2.tags.add(self.tag2)

    def test_seller_auction_listing(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data.get("results")), 2)

    def test_buyer_auction_listing(self):
        self.user.is_buyer = True
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_unauthenticated_access(self):
        self.client.logout()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_filter_by_LIVE_status(self):
        response = self.client.get(self.url, {"status": StatusChoices.LIVE})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data.get("results")), 1)
        self.assertEqual(
            response.data["results"][0]["product"], self.auction1.auction_name
        )

    def test_filter_by_UPCOMING_status(self):
        response = self.client.get(self.url, {"status": "Upcoming"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data.get("results")), 1)
        self.assertEqual(  # It is upcoming because the start_date is in future
            response.data["results"][0]["product"], self.auction2.auction_name
        )

    def test_search_by_tag(self):
        response = self.client.get(self.url, {"search": "Expensive"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data.get("results")), 1)
        self.assertEqual(
            response.data["results"][0]["product"], self.auction1.auction_name
        )

    def test_order_by_start_date(self):
        response = self.client.get(self.url, {"ordering": "start_date"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data.get("results")), 2)
        self.assertEqual(
            response.data["results"][0]["product"], self.auction1.auction_name
        )

    def test_order_by_max_price_desc(self):
        response = self.client.get(self.url, {"ordering": "-max_price"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data.get("results")), 2)
        self.assertEqual(
            response.data["results"][0]["product"], self.auction2.auction_name
        )

    def test_order_by_category_ascending(self):
        response = self.client.get(self.url + "?ordering=category")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data.get("results")), 2)
        self.assertEqual(
            response.data["results"][0]["product"], self.auction2.auction_name
        )

    def test_order_by_category_descending(self):
        response = self.client.get(self.url + "?ordering=-category")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data.get("results")), 2)
        self.assertEqual(response.data["results"][0]["category"], "Collectibles & Art")
        self.assertEqual(response.data["results"][1]["category"], "Automobiles")

    def test_order_by_tag_ascending(self):
        response = self.client.get(self.url + "?ordering=tags")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data.get("results")), 2)
        self.assertEqual(response.data["results"][0]["tags"][0], "Expensive")
        self.assertEqual(response.data["results"][1]["tags"][0], "Rare")

    def test_order_by_tag_descending(self):
        response = self.client.get(self.url + "?ordering=-tags")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data.get("results")), 2)
        self.assertEqual(response.data["results"][0]["tags"][0], "Rare")
        self.assertEqual(response.data["results"][1]["tags"][0], "Expensive")

    def test_auction_with_another_status(self):
        self.auction2.status = StatusChoices.COMPLETED
        self.auction2.save()
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data.get("results")), 1)
        self.assertEqual(
            response.data["results"][0]["product"], self.auction1.auction_name
        )

    def test_auction_with_start_date_in_future(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data.get("results")), 2)
        self.assertEqual(
            response.data["results"][0]["product"], self.auction2.auction_name
        )
        self.assertEqual(
            response.data["results"][1]["product"], self.auction1.auction_name
        )
        self.assertEqual(response.data["results"][0]["status"], "Upcoming")
        self.assertEqual(response.data["results"][1]["status"], StatusChoices.LIVE)

    def test_list_view_with_completed_status(self):
        self.auction1.status = StatusChoices.COMPLETED
        self.auction1.save()
        response = self.client.get(self.url, {"status": "Completed"})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn(
            "Select a valid choice. Completed is not one of the available choices.",
            response.data["errors"][0]["message"],
        )

    def test_auction_with_deleted_status(self):
        self.auction2.status = StatusChoices.DELETED
        self.auction2.save()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data.get("results")), 1)
        self.assertEqual(response.data["results"][0]["status"], StatusChoices.LIVE)
        self.assertEqual(
            response.data["results"][0]["product"], self.auction1.auction_name
        )


class SellerDashboardListViewTests(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = MockUser(user_id=uuid4())
        self.client.force_authenticate(user=self.user)
        self.url = reverse("seller-dashboard")

        self.category1 = CategoryFactory(name="Pet Supplies")
        self.category2 = CategoryFactory(name="Electronics")
        self.tag1 = TagFactory(name="Animals")
        self.tag2 = TagFactory(name="Water Device")

        self.auction1 = AuctionFactory(
            author=self.user.id,
            category=self.category1,
            status=StatusChoices.LIVE,
            accepted_bidders=AcceptedBiddersChoices.BOTH,
            accepted_locations="AL",
            start_date=timezone.now() - timedelta(days=5),
            end_date=timezone.now() + timedelta(days=1),
            max_price=100,
            quantity=1,
            auction_name="Awesome Pet Supplies Auction",
            description="Bid on the best pet supplies.",
        )
        self.auction1.tags.add(self.tag1, self.tag2)

        self.auction2 = AuctionFactory(
            author=self.user.id,
            category=self.category2,
            status=StatusChoices.LIVE,
            accepted_bidders=AcceptedBiddersChoices.COMPANY,
            accepted_locations="HR",
            start_date=timezone.now() - timedelta(days=2),
            end_date=timezone.now() + timedelta(days=1),
            max_price=200,
            quantity=2,
            auction_name="Old Electronics Auction",
            description="Bidding for various old electronics.",
        )
        self.auction2.tags.add(self.tag1)

        self.auction3 = AuctionFactory(
            author=uuid4(),
            category=self.category1,
            status=StatusChoices.LIVE,
            accepted_bidders=AcceptedBiddersChoices.COMPANY,
            accepted_locations="HR",
            start_date=timezone.now() - timedelta(days=2),
            end_date=timezone.now() + timedelta(days=1),
            max_price=300,
            quantity=3,
            auction_name="Auction from different user.",
            description="Simple auction.",
        )
        self.auction3.tags.add(self.tag1)
        self.bid = Bid.objects.create(
            author=self.user.id, auction=self.auction1, offer=500
        )

    def test_dashboard_list_success(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data.get("results")), 1)
        self.assertEqual(
            response.data["results"][0]["product"], "Awesome Pet Supplies Auction"
        )

    def test_dashboard_list_distinct(self):
        new_bid = Bid.objects.create(
            author=self.user.id, auction=self.auction1, offer=600
        )
        new_bid.save()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data.get("results")), 1)
        self.assertEqual(
            response.data["results"][0]["product"], "Awesome Pet Supplies Auction"
        )
        self.assertEqual(Bid.objects.count(), 2)


class AuctionRetrieveViewTests(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = MockUser(user_id=uuid4())
        self.client.force_authenticate(user=self.user)
        self.category1 = CategoryFactory(name="Pet Supplies")
        self.tag1 = TagFactory(name="Animals")
        self.tag2 = TagFactory(name="Pet Toys")

        self.auction = AuctionFactory(
            author=self.user.id,
            category=self.category1,
            status=StatusChoices.LIVE,
            accepted_bidders=AcceptedBiddersChoices.BOTH,
            accepted_locations=["GE", "AL", "HR"],
            start_date=timezone.now() - timedelta(days=5),
            end_date=timezone.now() + timedelta(days=1),
            max_price=100,
            quantity=1,
            auction_name="Awesome Pet Supplies Auction",
            description="Bid on the best pet supplies.",
        )
        self.auction.tags.add(self.tag1, self.tag2)
        self.auction_statistics = AuctionStatistics.objects.create(auction=self.auction)

        self.url = reverse("retrieve-auction", kwargs={"id": self.auction.id})

    def test_retrieve_auction_success(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["tags"][0], "Animals")
        self.assertEqual(response.data["tags"][1], "Pet Toys")
        self.assertEqual(
            response.data["accepted_locations"], ["Albania", "Georgia", "Croatia"]
        )
        self.assertIn("statistics", response.data)

    def test_retrieve_draft_auction_with_seller(self):
        self.user.is_seller = True
        self.auction.status = StatusChoices.DRAFT
        self.auction.save()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_retrieve_draft_auction_with_non_author_user(self):
        self.auction.status = StatusChoices.DRAFT
        self.auction.author = uuid4()
        self.auction.save()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_retrieve_auction_with_deleted_status(self):
        self.auction.status = StatusChoices.DELETED
        self.auction.save()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn("Not found.", response.data["errors"][0]["message"])


class AuctionDeleteViewTests(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = MockUser(user_id=uuid4())
        self.client.force_authenticate(user=self.user)

        self.category1 = CategoryFactory(name="Pet Supplies")
        self.tag1 = TagFactory(name="Animals")

        self.auction1 = AuctionFactory(
            author=self.user.id,
            category=self.category1,
            status=StatusChoices.LIVE,
            accepted_bidders=AcceptedBiddersChoices.BOTH,
            accepted_locations="AL",
            start_date=timezone.now() - timedelta(days=5),
            end_date=timezone.now() + timedelta(days=1),
            max_price=100,
            quantity=1,
            auction_name="Awesome Pet Supplies Auction",
            description="Bid on the best pet supplies.",
        )
        self.auction1.tags.add(self.tag1)
        self.url = reverse("delete-auction", kwargs={"id": self.auction1.id})

        self.auction2 = AuctionFactory(
            author=self.user.id,
            category=self.category1,
            status=StatusChoices.DRAFT,
            accepted_bidders=AcceptedBiddersChoices.BOTH,
            accepted_locations="AL",
            start_date=timezone.now() - timedelta(days=5),
            end_date=timezone.now() + timedelta(days=1),
            max_price=200,
            quantity=2,
            auction_name="Another Awesome Pet Supplies Auction",
            description="Bid on more pet supplies.",
        )
        self.auction2.tags.add(self.tag1)
        self.url2 = reverse("delete-auction", kwargs={"id": self.auction2.id})

    def test_delete_with_non_author_user(self):
        self.client.force_authenticate(user=MockUser(user_id=uuid4()))
        response = self.client.delete(self.url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertTrue(Auction.objects.filter(id=self.auction1.id).exists())

    def test_delete_with_seller_user_type(self):
        self.user.is_seller = True
        response = self.client.delete(self.url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertTrue(Auction.objects.filter(id=self.auction1.id).exists())

    def test_delete_draft_auction(self):
        response = self.client.delete(self.url2)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Auction.objects.filter(id=self.auction2.id).exists())

    def test_delete_live_auction(self):
        response = self.client.delete(self.url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.auction1.refresh_from_db()
        self.assertEqual(self.auction1.status, StatusChoices.DELETED)


class BookmarkListViewTests(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = MockUser(user_id=uuid4())
        self.client.force_authenticate(user=self.user)
        self.url = reverse("list-bookmark")

        self.category1 = CategoryFactory(name="Pet Supplies")
        self.category2 = CategoryFactory(name="Electronics")
        self.tag1 = TagFactory(name="Animals")
        self.tag2 = TagFactory(name="Water Device")

        self.auction1 = AuctionFactory(
            author=self.user.id,
            category=self.category1,
            status=StatusChoices.LIVE,
            accepted_bidders=AcceptedBiddersChoices.BOTH,
            accepted_locations="AL",
            start_date=timezone.now() - timedelta(days=5),
            end_date=timezone.now() + timedelta(days=1),
            max_price=100,
            quantity=1,
            auction_name="Awesome Pet Supplies Auction",
            description="Bid on the best pet supplies.",
            condition=ConditionChoices.NEW,
        )
        self.auction1.tags.add(self.tag1, self.tag2)

        self.auction2 = AuctionFactory(
            author=self.user.id,
            category=self.category2,
            status=StatusChoices.COMPLETED,
            accepted_bidders=AcceptedBiddersChoices.COMPANY,
            accepted_locations="HR",
            start_date=timezone.now() - timedelta(days=2),
            end_date=timezone.now() - timedelta(days=1),
            max_price=200,
            quantity=2,
            auction_name="Old Electronics Auction",
            description="Bidding for various old electronics.",
            condition=ConditionChoices.NEW,
        )
        self.auction2.tags.add(self.tag1)

        self.bookmark1 = BookmarkFactory(user_id=self.user.id, auction=self.auction1)
        self.bookmark2 = BookmarkFactory(user_id=self.user.id, auction=self.auction2)

    def test_bookmark_listing(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data.get("results")), 2)

    def test_unauthenticated_access(self):
        self.client.logout()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_filter_by_status(self):
        response = self.client.get(self.url, {"status": StatusChoices.LIVE})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data.get("results")), 1)
        self.assertEqual(
            response.data["results"][0]["auction"]["product"], self.auction1.auction_name
        )

    def test_filter_by_invalid_status(self):
        response = self.client.get(self.url, {"status": "invalid_status"})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_filter_by_condition(self):
        self.auction1.condition = ConditionChoices.USED_GOOD
        self.auction1.save()

        response = self.client.get(self.url, {"condition": ConditionChoices.USED_GOOD})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data.get("results")), 1)
        self.assertEqual(
            response.data["results"][0]["auction"]["product"], self.auction1.auction_name
        )

    def test_filter_by_accepted_bidders(self):
        response = self.client.get(
            self.url, {"accepted_bidders": AcceptedBiddersChoices.BOTH}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data.get("results")), 1)
        self.assertEqual(
            response.data["results"][0]["auction"]["product"], self.auction1.auction_name
        )

    def test_filter_by_accepted_locations(self):
        response = self.client.get(
            self.url, {"accepted_locations": self.auction1.accepted_locations}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data.get("results")), 1)
        self.assertEqual(
            response.data["results"][0]["auction"]["product"], self.auction1.auction_name
        )

    def test_filter_by_currency(self):
        response = self.client.get(self.url, {"currency": self.auction1.currency})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data.get("results")), 1)
        self.assertEqual(
            response.data["results"][0]["auction"]["product"], self.auction1.auction_name
        )

    def test_filter_by_max_price(self):
        response = self.client.get(self.url, {"max_price": 100})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data.get("results")), 1)
        self.assertEqual(
            response.data["results"][0]["auction"]["product"], self.auction1.auction_name
        )

    def test_filter_by_min_price(self):
        response = self.client.get(self.url, {"min_price": 101})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data.get("results")), 1)
        self.assertEqual(
            response.data["results"][0]["auction"]["product"], self.auction2.auction_name
        )

    def test_filter_by_start_date(self):
        response = self.client.get(
            self.url, {"start_date": str(self.auction1.start_date.date())}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data.get("results")), 2)

    def test_filter_by_end_date(self):
        response = self.client.get(self.url, {"end_date": (timezone.now()).date()})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data.get("results")), 1)

    def test_filter_by_both_dates(self):
        response = self.client.get(
            self.url,
            {
                "start_date": "2000-01-01",
                "end_date": "2040-01-01",
            },
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data.get("results")), 2)

    def test_filter_by_category(self):
        response = self.client.get(self.url, {"category": self.auction1.category.name})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data.get("results")), 1)
        self.assertEqual(
            response.data["results"][0]["auction"]["product"], self.auction1.auction_name
        )

    def test_filter_by_invalid_category(self):
        response = self.client.get(self.url, {"category": "Invalid Category"})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_user_can_only_list_their_bookmarks(self):
        author = uuid4()
        category = CategoryFactory(name="Other")
        auction_from_another_user = AuctionFactory(
            author=author,
            auction_name="Pet auction from another user",
            category=category,
        )
        BookmarkFactory(user_id=author, auction=auction_from_another_user)

        # Listing test
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data.get("results")), 2)
        self.assertNotEqual(
            response.data["results"][0]["auction"]["product"],
            auction_from_another_user.auction_name,
        )
        self.assertNotEqual(
            response.data["results"][1]["auction"]["product"],
            auction_from_another_user.auction_name,
        )

        # Filtering
        response = self.client.get(self.url, {"category": "Other"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data.get("results")), 0)

        # Searching
        # Name of the auction that is created in this test case
        # includes 'Pet', similarily the name of auction1 includes 'Pet'
        response = self.client.get(self.url + "?search=Pet")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data.get("results")), 1)
        print()
        self.assertNotEqual(
            response.data["results"][0]["auction"]["product"],
            auction_from_another_user.auction_name,
        )
        self.assertEqual(
            response.data["results"][0]["auction"]["product"],
            self.auction1.auction_name,
        )

        # Ordering
        response = self.client.get(self.url + "?ordering=start_date")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data.get("results")), 2)
        self.assertEqual(
            response.data["results"][0]["auction"]["product"], self.auction2.auction_name
        )
        self.assertEqual(
            response.data["results"][1]["auction"]["product"], self.auction1.auction_name
        )


class CreateBookmarkViewTestCase(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.user_payload = {
            "user_id": str(uuid4()),
            "email": "user@example.com",
            "is_verified": True,
            "user_type": "Buyer",
            "user_profile_type": "Individual",
        }
        self.user_proxy = UserProxy(self.user_payload)

        self.category = Category.objects.create(name="Test Category")

        self.auction = Auction.objects.create(
            author=self.user_proxy.id,
            auction_name="Test Auction",
            description="This is a test auction.",
            category=self.category,
            start_date=date.today(),
            end_date=date.today(),
            max_price=1000.00,
            quantity=1,
            accepted_bidders="Both",
            status="draft",
            currency="GEL",
            condition="New",
        )

        patcher = patch(
            "auction.authentication.custom_jwt_auth.CustomJWTAuthentication.authenticate"
        )
        self.mock_authenticate = patcher.start()
        self.mock_authenticate.return_value = (self.user_proxy, None)
        self.addCleanup(patcher.stop)

        self.url = reverse("create-bookmark")

    def test_create_bookmark_success(self):
        data = {"auction_id": str(self.auction.id)}
        response = self.client.post(self.url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn("bookmark_id", response.data)
        self.assertEqual(response.data["user_id"], self.user_payload["user_id"])
        self.assertEqual(str(response.data["auction_id"]), str(self.auction.id))
        self.assertEqual(Bookmark.objects.count(), 1)

    def test_create_bookmark_duplicate(self):
        Bookmark.objects.create(user_id=self.user_proxy.id, auction=self.auction)

        data = {"auction_id": str(self.auction.id)}
        response = self.client.post(self.url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.data["errors"][0]["message"], "This auction is already bookmarked."
        )

    def test_create_bookmark_invalid_auction(self):
        data = {"auction_id": str(uuid4())}
        response = self.client.post(self.url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(
            str(response.data["errors"][0]["message"]),
            "Not found.",
        )


class CreateLiveAuctionViewTests(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = MockUser(user_id=uuid4())
        self.client.force_authenticate(user=self.user)
        self.url = reverse("create-live-auction")

        self.category = CategoryFactory(name="Collectibles & Art")
        self.tag1 = TagFactory(name="Luxury")
        self.tag2 = TagFactory(name="Rare")

        self.frequently_used_data = {
            "auction_name": "Luxury Painting Auction",
            "description": "Auctioning a rare and expensive painting.",
            "category": self.category.name,
            "start_date": timezone.now() + timedelta(days=1),
            "end_date": timezone.now() + timedelta(days=5),
            "max_price": 5000.00,
            "quantity": 1,
            "accepted_bidders": AcceptedBiddersChoices.BOTH,
            "accepted_locations": ["US"],
            "tags": [{"name": self.tag1.name}, {"name": self.tag2.name}],
            "condition": ConditionChoices.NEW,
        }

    def test_create_auction_success(self):
        data = self.frequently_used_data
        response = self.client.post(self.url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["auction_name"], data["auction_name"])
        self.assertEqual(response.data["status"], "Upcoming")  # Start date is in future

    def test_unauthenticated_user_cannot_create_auction(self):
        self.client.logout()
        data = self.frequently_used_data
        response = self.client.post(self.url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_missing_required_fields(self):
        data = self.frequently_used_data
        data.pop("auction_name")
        response = self.client.post(self.url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("auction_name", response.data["errors"][0]["field_name"])

    def test_end_date_before_start_date(self):
        data = self.frequently_used_data
        data["start_date"] = timezone.now() + timedelta(days=5)
        data["end_date"] = timezone.now() + timedelta(days=1)
        response = self.client.post(self.url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("end_date", response.data["errors"][0]["field_name"])
        self.assertIn(
            "End date must be after the start date.",
            response.data["errors"][0]["message"],
        )

    def test_start_date_in_past(self):
        data = self.frequently_used_data
        data["start_date"] = timezone.now() - timedelta(days=1)
        response = self.client.post(self.url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("start_date", response.data["errors"][0]["field_name"])
        self.assertIn(
            "Start date cannot be in the past.", response.data["errors"][0]["message"]
        )

    def test_invalid_max_price(self):
        data = self.frequently_used_data
        data["max_price"] = -1
        response = self.client.post(self.url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("max_price", response.data["errors"][0]["field_name"])
        self.assertIn(
            "Max price must be greater than 0.", response.data["errors"][0]["message"]
        )

    def test_invalid_accepted_bidders_choice(self):
        data = self.frequently_used_data
        data["accepted_bidders"] = "Invalid"
        response = self.client.post(self.url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("accepted_bidders", response.data["errors"][0]["field_name"])

    def test_create_auction_with_invalid_tag(self):
        data = self.frequently_used_data
        data["tags"] = [{"name": "invalid"}]
        response = self.client.post(self.url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("tags", response.data["errors"][0]["field_name"])

    def test_create_auction_with_invalid_category(self):
        data = self.frequently_used_data
        data["category"] = "invalid"
        response = self.client.post(self.url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("category", response.data["errors"][0]["field_name"])

    def test_user_has_no_country_in_profile(self):
        self.user.country = ""
        data = self.frequently_used_data
        response = self.client.post(self.url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn(
            "User must set a country in their profile before proceeding.",
            response.data["errors"][0]["message"],
        )

    def test_quantity_negative_value(self):
        data = self.frequently_used_data
        data["quantity"] = -1
        response = self.client.post(self.url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("quantity", response.data["errors"][0]["field_name"])

    def test_read_only_fields(self):
        data = self.frequently_used_data
        data["id"] = uuid4()
        data["status"] = StatusChoices.DRAFT
        data["author"] = uuid4()
        response = self.client.post(self.url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_country_codes_are_translated_to_country_names(self):
        data = self.frequently_used_data
        response = self.client.post(self.url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(
            Auction.objects.last().accepted_locations[0].name, "United States of America"
        )

    def test_invalid_condition(self):
        data = self.frequently_used_data
        data["condition"] = "Invalid"
        response = self.client.post(self.url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("condition", response.data["errors"][0]["field_name"])

    def test_invalid_date(self):
        data = self.frequently_used_data
        data["start_date"] = timezone.now() - timedelta(days=1)
        data["end_date"] = timezone.now() + timedelta(days=1)
        response = self.client.post(self.url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_auction_with_empty_tags(self):
        data = self.frequently_used_data
        data["tags"] = []
        response = self.client.post(self.url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn(
            "Tags are required, make sure to include them.",
            response.data["errors"][0]["message"],
        )

    def test_create_auction_with_empty_accepted_locations(self):
        data = self.frequently_used_data
        data["accepted_locations"] = []
        response = self.client.post(self.url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn("accepted_locations", response.data)
        self.assertEqual(response.data.get("accepted_locations"), ["International"])

    @patch("auction.serializers.transaction.atomic")
    def test_transaction_atomic_on_error(self, mock_atomic):
        mock_atomic.side_effect = IntegrityError()
        data = self.frequently_used_data

        response = self.client.post(self.url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn(
            "There was an error during the creation of an auction",
            response.data["errors"][0]["message"],
        )
        self.assertEqual(Auction.objects.count(), 0)

    def test_validate_start_date_naive_date(self):
        data = self.frequently_used_data
        data["start_date"] = datetime.now() + timedelta(days=1)
        self.assertIsNone(data["start_date"].tzinfo)
        response = self.client.post(self.url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        date = Auction.objects.last().start_date
        self.assertIsNotNone(date.tzinfo)
        self.assertTrue(timezone.is_aware(date))

    def test_validate_end_date_naive_date(self):
        data = self.frequently_used_data
        data["end_date"] = datetime.now() + timedelta(days=1)
        self.assertIsNone(data["end_date"].tzinfo)
        response = self.client.post(self.url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        date = Auction.objects.last().end_date
        self.assertIsNotNone(date.tzinfo)
        self.assertTrue(timezone.is_aware(date))

    @patch("auction.views.CreateLiveAuctionView.notify_auction")
    def test_notification_sent_on_successful_auction_creation(self, mock_notify):
        data = self.frequently_used_data
        response = self.client.post(self.url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        mock_notify.assert_called_once_with(response.data)

    @patch("auction.views.CreateLiveAuctionView.notify_auction")
    def test_notification_error_handling(self, mock_notify):
        mock_notify.side_effect = Exception("Notification error")
        data = self.frequently_used_data

        response = self.client.post(self.url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn(
            "Auction created successfully, but failed to send notifications: Notification error",
            response.data.get("warning"),
        )

    def test_create_auction_sets_correct_status(self):
        data = self.frequently_used_data
        response = self.client.post(self.url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["status"], "Upcoming")  # Start date is in future

    def test_get_auction_status_raises_error_for_base_class(self):
        view = BaseAuctionView()
        with self.assertRaises(NotImplementedError):
            view.get_auction_status()

    def test_get_auction_status_returns_live_for_create_live_auction_view(self):
        view = CreateLiveAuctionView()
        self.assertEqual(view.get_auction_status(), StatusChoices.LIVE)

    def test_get_notifications_returns_correct_values_for_live_auction_view(self):
        view = CreateLiveAuctionView()
        data_to_compare = {
            "buyer": True,
            "sellers": True,
        }
        self.assertEqual(view.get_notifications(), data_to_compare)

    def test_get_auction_status_returns_draft_for_create_draft_auction_view(self):
        view = CreateDraftAuctionView()
        self.assertEqual(view.get_auction_status(), StatusChoices.DRAFT)

    def test_get_notifications_returns_correct_values_for_draft_view(self):
        view = CreateDraftAuctionView()
        data_to_compare = {
            "buyer": True,
            "sellers": False,
        }
        self.assertEqual(view.get_notifications(), data_to_compare)


class UpdateLiveAuctionViewTests(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = MockUser(user_id=uuid4())
        self.client.force_authenticate(user=self.user)

        self.category = CategoryFactory(name="Collectibles & Art")
        self.tag1 = TagFactory(name="Luxury")
        self.tag2 = TagFactory(name="Rare")

        self.auction = Auction.objects.create(
            author=self.user.id,
            auction_name="Original Auction",
            description="Original description",
            category=self.category,
            start_date=timezone.now() + timedelta(days=2),
            end_date=timezone.now() + timedelta(days=5),
            max_price=1000.00,
            quantity=1,
            accepted_bidders=AcceptedBiddersChoices.BOTH,
            condition=ConditionChoices.NEW,
        )
        self.auction.tags.set([self.tag1, self.tag2])

        self.url = reverse("update-auction", kwargs={"id": self.auction.id})

        self.update_data = {
            "auction_name": "Updated Luxury Painting Auction",
            "description": "Updated description for the auction.",
            "category": self.category.name,
            "end_date": timezone.now() + timedelta(days=7),
            "max_price": 6000.00,
            "quantity": 2,
            "accepted_bidders": AcceptedBiddersChoices.BOTH,
            "accepted_locations": ["US"],
            "tags": [{"name": self.tag1.name}, {"name": self.tag2.name}],
            "currency": "GEL",
            "condition": ConditionChoices.USED_GOOD,
        }

    def test_update_auction_success(self):
        response = self.client.patch(self.url, self.update_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["auction_name"], self.update_data["auction_name"])
        self.assertEqual(response.data["description"], self.update_data["description"])
        self.assertEqual(response.data["category"], self.update_data["category"])
        self.assertEqual(response.data["max_price"], "6000.00")
        self.assertEqual(response.data["quantity"], self.update_data["quantity"])
        self.assertIsNotNone(response.data["tags"])

    def test_unauthenticated_user_cannot_update_auction(self):
        self.client.logout()
        response = self.client.patch(self.url, self.update_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_non_author_cannot_update_auction(self):
        different_user = MockUser(user_id=uuid4())
        self.client.force_authenticate(user=different_user)
        response = self.client.patch(self.url, self.update_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_cannot_update_started_auction(self):
        # Set auction start date to past
        self.auction.start_date = timezone.now() - timedelta(days=1)
        self.auction.save()

        response = self.client.patch(self.url, self.update_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn(
            "Cannot modify core auction parameters after the auction has started",
            response.data["errors"][0]["message"],
        )

    def test_cannot_update_ended_auction(self):
        self.auction.end_date = timezone.now() - timedelta(days=1)
        self.auction.save()

        response = self.client.patch(self.url, self.update_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn(
            "Cannot update auction that has already ended",
            response.data["errors"][0]["message"],
        )

    def test_can_update_start_date_before_auction_starts(self):
        data = self.update_data.copy()
        data["start_date"] = timezone.now() + timedelta(days=4)
        response = self.client.patch(self.url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_cannot_update_start_date_before_auction_starts(self):
        """
        Test that start date can not be set to be more than the end_date
        even if the auction has not started yet.
        """
        data = self.update_data.copy()
        data["start_date"] = timezone.now() + timedelta(days=100)
        response = self.client.patch(self.url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.data["errors"][0]["message"],
            "End date must be after the start date.",
        )

    def test_end_date_validation(self):
        data = self.update_data.copy()
        data["end_date"] = timezone.now() + timedelta(hours=1)
        response = self.client.patch(self.url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.data["errors"][0]["message"],
            "End date must be after the start date.",
        )
        self.assertIn("end_date", response.data["errors"][0]["field_name"])

    def test_invalid_max_price(self):
        data = self.update_data.copy()
        data["max_price"] = -100
        response = self.client.patch(self.url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("max_price", response.data["errors"][0]["field_name"])
        self.assertIn(
            "Max price must be greater than 0", response.data["errors"][0]["message"]
        )

    def test_can_update_currency(self):
        data = self.update_data.copy()
        data["currency"] = "EUR"
        response = self.client.patch(self.url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_can_update_condition(self):
        data = self.update_data.copy()
        data["condition"] = ConditionChoices.USED_ACCEPTABLE
        response = self.client.patch(self.url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_update_tags(self):
        new_tag = TagFactory(name="Compact")
        data = self.update_data.copy()
        data["tags"] = [{"name": new_tag.name}]
        response = self.client.patch(self.url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["tags"]), 1)
        self.assertEqual(response.data["tags"][0], new_tag.name)

    def test_update_with_empty_tags(self):
        data = self.update_data.copy()
        data["tags"] = []
        response = self.client.patch(self.url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn(
            "Tags are required, make sure to include them",
            response.data["errors"][0]["message"],
        )

    def test_update_with_invalid_category(self):
        data = self.update_data.copy()
        data["category"] = "Invalid Category"
        response = self.client.patch(self.url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("category", response.data["errors"][0]["field_name"])

    def test_partial_update(self):
        partial_data = {
            "auction_name": "Partially Updated Auction",
            "description": "New description only",
        }
        response = self.client.patch(self.url, partial_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["auction_name"], partial_data["auction_name"])
        self.assertEqual(response.data["description"], partial_data["description"])

    @patch("auction.serializers.transaction.atomic")
    def test_transaction_atomic_on_error(self, mock_atomic):
        mock_atomic.side_effect = IntegrityError()
        response = self.client.patch(self.url, self.update_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn(
            "There was an error during the update of the auction. " "Please try again.",
            response.data["errors"][0]["message"],
        )

    def test_country_codes_are_translated_to_country_names(self):
        data = self.update_data.copy()
        response = self.client.patch(self.url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            Auction.objects.get(id=self.auction.id).accepted_locations[0].name,
            "United States of America",
        )
