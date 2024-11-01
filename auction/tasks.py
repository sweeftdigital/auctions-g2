import logging
from typing import Any, Dict

from celery.exceptions import MaxRetriesExceededError
from django.conf import settings
from django.db import transaction
from django.utils import timezone

from auction.models import Auction
from auction.models.auction import StatusChoices
from auctions.celery import app

logger = logging.getLogger(__name__)

BATCH_SIZE = getattr(settings, "AUCTION_BATCH_SIZE", 1000)
MAX_RETRIES = getattr(settings, "AUCTION_TASK_MAX_RETRIES", 3)
RETRY_DELAY = getattr(settings, "AUCTION_TASK_RETRY_DELAY", 300)  # 5 minutes


@app.task(
    bind=True,
    autoretry_for=(Exception,),
    retry_kwargs={"max_retries": MAX_RETRIES, "countdown": RETRY_DELAY},
    acks_late=True,
)
def complete_expired_auctions(self) -> Dict[str, Any]:
    """
    Complete auctions that have passed their end date and update their statistics.
    Uses efficient batch processing and database-level operations.

    Returns:
        Dict containing success status, number of auctions completed, and processing timestamp

    Raises:
        MaxRetriesExceededError: When maximum retries are exceeded
        Exception: For other unexpected errors
    """
    current_time = timezone.now()
    metrics = {"auctions_processed": 0, "errors": 0}

    try:
        while True:
            chunk_count = process_auction_chunk(current_time)
            if not chunk_count:
                break
            metrics["auctions_processed"] += chunk_count

        logger.info(
            "Auction completion task finished",
            extra={"metrics": metrics, "task_id": self.request.id},
        )
        return {
            "success": True,
            "metrics": metrics,
            "processed_at": current_time.isoformat(),
        }

    except Exception as e:
        metrics["errors"] += 1
        logger.error(
            "Error in complete_expired_auctions task",
            exc_info=True,
            extra={"task_id": self.request.id, "metrics": metrics},
        )

        if self.request.retries >= MAX_RETRIES:
            raise MaxRetriesExceededError(
                f"Maximum retries ({MAX_RETRIES}) exceeded for auction completion task"
            )
        raise self.retry(exc=e)


def process_auction_chunk(current_time: timezone.datetime) -> int:
    """
    Process and update expired auctions in batches, returning the count of updated auctions.
    Uses efficient batch processing with ID-based pagination.
    """
    try:
        with transaction.atomic():
            # First, get the IDs of auctions to update
            auction_ids = list(
                Auction.objects.filter(
                    status=StatusChoices.LIVE, end_date__lte=current_time
                )
                .select_for_update(skip_locked=True)
                .values_list("id", flat=True)[:BATCH_SIZE]
            )

            if not auction_ids:
                return 0

            # Then perform the update on the selected IDs
            update_count = Auction.objects.filter(id__in=auction_ids).update(
                status=StatusChoices.COMPLETED, updated_at=current_time
            )

            return update_count

    except Exception as e:
        logger.error(f"Error processing auction chunk: {e}", exc_info=True)
        return 0
