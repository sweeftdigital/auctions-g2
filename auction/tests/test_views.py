import uuid

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
    AcceptedLocations,
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

        self.category1 = CategoryFactory()
        self.category2 = CategoryFactory()
        self.tag1 = TagFactory()
        self.tag2 = TagFactory()

        self.auction1 = AuctionFactory(
            author=self.user.id,
            category=self.category1,
            status=StatusChoices.ACTIVE,
            accepted_bidders=AcceptedBiddersChoices.BOTH,
            accepted_locations=AcceptedLocations.MY_LOCATION,
        )
        self.auction1.tags.add(self.tag1, self.tag2)

        self.auction2 = AuctionFactory(
            author=self.user.id,
            category=self.category2,
            status=StatusChoices.COMPLETED,
            accepted_bidders=AcceptedBiddersChoices.COMPANY,
            accepted_locations=AcceptedLocations.INTERNATIONAL,
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
        response = self.client.get(self.url, {"accepted_locations": "My Location"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["product"], self.auction1.auction_name)

    def test_filter_by_currency(self):
        response = self.client.get(self.url, {"currency": self.auction1.currency})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["product"], self.auction1.auction_name)
