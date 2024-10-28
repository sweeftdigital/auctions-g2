from abc import ABC, abstractmethod

from django.db import transaction

from auction.models.auction import Auction
from bid.models.bid import Bid


class EventHandler(ABC):
    @abstractmethod
    def handle(self, event_body):
        pass


class BuyerDeletedHandler(EventHandler):
    """
    Handles the 'user deleted' event that is published from accounts service.

    This method processes the deletion of a user by updating or deleting their associated auctions.

    - All auctions that do not have the status "Draft" will be updated to have a status of "Deleted".
    - All auctions with the status "Draft" will be permanently deleted from the database.
    """

    def handle(self, event_body):
        print(f"Handling user deleted event: {event_body}")
        user_id = event_body.get("user_id")

        try:
            with transaction.atomic():
                # Update all auctions that do not have the "Draft" status to "Deleted"
                # for the auctions created by the user specified in event_body
                Auction.objects.filter(author=user_id).exclude(status="Draft").update(
                    status="Deleted"
                )

                # Delete all auctions that have status of "Draft" for that user
                Auction.objects.filter(author=user_id, status="Draft").delete()
        except Exception as e:
            print(f"Error processing Buyer deletion: {e}")
            raise


class SellerDeletedHandler(EventHandler):
    def handle(self, event_body):
        print(f"Handling user deleted event: {event_body}")
        user_id = event_body.get("user_id")

        try:
            with transaction.atomic():
                # Update all bid statuses to "Deleted" that belongs to the deleted user
                Bid.objects.filter(author=user_id).update(status="Deleted")
        except Exception as e:
            print(f"Error processing Buyer deletion: {e}")
            raise
