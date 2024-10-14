from unittest.mock import patch
from uuid import uuid4

from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient, APITestCase

from auction.factories.model_factories import AuctionFactory
from auction.models import Auction
from auction.models.auction import AcceptedBiddersChoices, StatusChoices
from bid.models import Bid


class MockUser:
    def __init__(
        self, user_id=None, is_seller=False, is_individual=False, is_company=False
    ):
        self.id = user_id or uuid4()
        self.is_authenticated = True
        self.is_seller = is_seller
        self._is_individual = is_individual
        self._is_company = is_company
        self.full_name = "Test User"

    def is_individual(self):
        return self._is_individual

    def is_company(self):
        return self._is_company


class CreateBidViewTests(APITestCase):

    def setUp(self):
        self.client = APIClient()
        self.user = MockUser(user_id=uuid4(), is_seller=True, is_individual=True)
        self.client.force_authenticate(user=self.user)

        self.auction = AuctionFactory(
            author=self.user.id,
            status=StatusChoices.LIVE,
            accepted_bidders=AcceptedBiddersChoices.BOTH,
            start_date=timezone.now() - timezone.timedelta(days=1),
            end_date=timezone.now() + timezone.timedelta(days=1),
        )

        self.url = reverse("create-bid", kwargs={"auction_id": self.auction.id})

    @patch("auction.models.Auction.objects.get")
    @patch("bid.views.CreateBidView.notify_auction_group")
    def test_create_bid_success(self, mock_notify, mock_get_auction):
        mock_get_auction.return_value = self.auction
        data = {
            "offer": 100,
            "description": "A test bid",
            "delivery_fee": 10.00,
            "images": [],
        }
        response = self.client.post(self.url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Bid.objects.count(), 1)

        mock_notify.assert_called_once()

    @patch("auction.models.Auction.objects.get")
    def test_create_bid_auction_not_found(self, mock_get_auction):
        mock_get_auction.side_effect = Auction.DoesNotExist

        data = {
            "offer": 100,
            "description": "A test bid",
            "delivery_fee": 10.00,
            "images": [],
        }

        response = self.client.post(self.url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # Ensure the response contains the correct error structure
        self.assertIn("errors", response.data)
        self.assertIn(
            "non_field_errors", [error["field_name"] for error in response.data["errors"]]
        )
        self.assertEqual(response.data["errors"][0]["message"], "Auction does not exist.")
