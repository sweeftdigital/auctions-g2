import uuid
from datetime import datetime, timedelta

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient, APITestCase

from auction.factories.model_factories import (
    AuctionFactory,
    CategoryFactory,
    TagFactory,
)
from auction.models.auction import (
    AcceptedBiddersChoices,
    ConditionChoices,
    StatusChoices,
)


class MockUser:
    def __init__(self, user_id):
        self.id = user_id
        self.is_authenticated = True


class AuctionListViewTests(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = MockUser(user_id=uuid.uuid4())
        self.client.force_authenticate(user=self.user)
        self.url = reverse("auction-list")

        self.category1 = CategoryFactory(name="Pet Supplies")
        self.category2 = CategoryFactory(name="Electronics")
        self.tag1 = TagFactory()
        self.tag2 = TagFactory()

        self.auction1 = AuctionFactory(
            author=self.user.id,
            category=self.category1,
            status=StatusChoices.ACTIVE,
            accepted_bidders=AcceptedBiddersChoices.BOTH,
            accepted_locations="Albania",
            start_date=datetime.now() - timedelta(days=5),
            end_date=datetime.now() + timedelta(days=1),
            max_price=100,
            auction_name="Awesome Pet Supplies Auction",
            description="Bid on the best pet supplies.",
        )
        self.auction1.tags.add(self.tag1, self.tag2)

        self.auction2 = AuctionFactory(
            author=self.user.id,
            category=self.category2,
            status=StatusChoices.COMPLETED,
            accepted_bidders=AcceptedBiddersChoices.COMPANY,
            accepted_locations="Croatia",
            start_date=datetime.now() - timedelta(days=1),
            end_date=datetime.now() - timedelta(days=2),
            max_price=200,
            auction_name="Old Electronics Auction",
            description="Bidding for various old electronics.",
        )
        self.auction2.tags.add(self.tag1)

    def test_auction_listing(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

    def test_unauthenticated_access(self):
        self.client.logout()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_filter_by_status(self):
        response = self.client.get(self.url, {"status": StatusChoices.ACTIVE})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["product"], self.auction1.auction_name)

    def test_filter_by_invalid_status(self):
        response = self.client.get(self.url, {"status": "invalid_status"})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_filter_by_condition(self):
        self.auction1.condition = ConditionChoices.NEW
        self.auction1.save()

        response = self.client.get(self.url, {"condition": ConditionChoices.NEW})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["product"], self.auction1.auction_name)

    def test_filter_by_accepted_bidders(self):
        response = self.client.get(
            self.url, {"accepted_bidders": AcceptedBiddersChoices.BOTH}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["product"], self.auction1.auction_name)

    def test_filter_by_accepted_locations(self):
        response = self.client.get(
            self.url, {"accepted_locations": self.auction1.accepted_locations}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["product"], self.auction1.auction_name)

    def test_filter_by_currency(self):
        response = self.client.get(self.url, {"currency": self.auction1.currency})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["product"], self.auction1.auction_name)

    def test_filter_by_max_price(self):
        response = self.client.get(self.url, {"max_price": 100})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["product"], self.auction1.auction_name)

    def test_filter_by_min_price(self):
        response = self.client.get(self.url, {"min_price": 101})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["product"], self.auction2.auction_name)

    def test_filter_by_start_date(self):
        response = self.client.get(
            self.url, {"start_date": str(self.auction1.start_date.date())}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

    def test_filter_by_end_date(self):
        response = self.client.get(self.url, {"end_date": (datetime.now()).date()})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_filter_by_both_dates(self):
        response = self.client.get(
            self.url,
            {
                "start_date": "2000-01-01",
                "end_date": "2040-01-01",
            },
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

    def test_filter_by_category(self):
        response = self.client.get(self.url, {"category": self.category1.name})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["product"], self.auction1.auction_name)

    def test_filter_by_invalid_category(self):
        response = self.client.get(self.url, {"category": "Invalid Category"})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_search_by_auction_name(self):
        response = self.client.get(self.url, {"search": "Awesome Pet Supplies Auction"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["product"], self.auction1.auction_name)

    def test_search_by_description(self):
        response = self.client.get(
            self.url, {"search": "Bidding for various old electronics."}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["product"], self.auction2.auction_name)

    def test_search_by_partial_match(self):
        response = self.client.get(self.url, {"search": "Awesome"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["product"], self.auction1.auction_name)

    def test_search_by_no_results(self):
        response = self.client.get(self.url, {"search": "Nonexistent Auction"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)
