import logging
from datetime import datetime
from time import time
from typing import Any, Dict
from uuid import UUID

from celery import shared_task
from celery.exceptions import MaxRetriesExceededError
from django.conf import settings
from django.db import transaction
from django.db.models import Q
from django.utils import timezone

from auction.models import Auction
from auction.models.auction import StatusChoices
from auctions.celery import app
from bid.models import Bid
from bid.models.bid import StatusChoices as BidStatusChoices

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


@shared_task(
    name="auctions.tasks.revoke_auction_bids",
    autoretry_for=(Exception,),
    max_retries=MAX_RETRIES,
    retry_backoff=True,
)
def revoke_auction_bids(auction_id: str, chunk_size: int = BATCH_SIZE) -> Dict[str, Any]:
    """
    Revoke all bids associated with a canceled auction using cursor-based pagination.

    Args:
        auction_id (str): The UUID of the canceled auction
        chunk_size (int): Number of bids to process in each chunk

    Returns:
        Dict[str, Any]: A dictionary containing the number of bids updated and timing metrics
    """
    start_time = time()
    chunk_times = []

    try:
        total_updated = 0
        last_created_at = None
        chunk_number = 0

        if isinstance(auction_id, str):
            auction_id = UUID(auction_id)

        logger.info(f"Starting bid revocation for auction {auction_id}")

        with transaction.atomic():
            auction = Auction.objects.select_for_update().get(id=auction_id)
            logger.info(f"Auction status: {auction.status}")

            current_status = str(auction.status).upper()
            expected_status = str(StatusChoices.CANCELED).upper()

            logger.info(
                f"Comparing status: current={current_status}, expected={expected_status}"
            )

            if current_status != expected_status:
                error_msg = f"Cannot revoke bids - auction status is {current_status}, expected {expected_status}"
                logger.warning(error_msg)
                return {
                    "auction_id": auction_id,
                    "bids_revoked": 0,
                    "status": "error",
                    "message": error_msg,
                    "timing": {
                        "total_time_seconds": round(time() - start_time, 3),
                        "started_at": datetime.fromtimestamp(start_time).isoformat(),
                        "completed_at": datetime.fromtimestamp(time()).isoformat(),
                    },
                }

        # Statuses to process
        bids_to_process = [
            BidStatusChoices.PENDING,
            BidStatusChoices.APPROVED,
            BidStatusChoices.REJECTED,
        ]

        while True:
            chunk_start = time()
            with transaction.atomic():
                # Build filter conditions
                filters = Q(auction=auction_id) & Q(status__in=bids_to_process)

                # Add cursor condition if we have a last timestamp
                if last_created_at:
                    filters &= Q(created_at__gt=last_created_at)

                # Get next batch of bids
                bid_chunk = (
                    Bid.objects.filter(filters)
                    .order_by(
                        "created_at", "id"
                    )  # Compound ordering for stable pagination
                    .values_list("id", "created_at")[:chunk_size]
                )

                # Materialize the chunk and log count
                bid_chunk = list(bid_chunk)
                logger.info(f"Found {len(bid_chunk)} bids to process in this chunk")

                if not bid_chunk:
                    logger.info("No more bids to process")
                    break

                # Separate IDs and get last timestamp
                bid_ids = [bid[0] for bid in bid_chunk]
                last_created_at = bid_chunk[-1][1]

                # Update this chunk
                chunk_updated = Bid.objects.filter(id__in=bid_ids).update(
                    status=BidStatusChoices.REVOKED, updated_at=timezone.now()
                )

                total_updated += chunk_updated
                chunk_number += 1

                logger.info(f"Updated {chunk_updated} bids in chunk {chunk_number}")

                # Record chunk timing
                chunk_end = time()
                chunk_times.append(
                    {
                        "chunk": chunk_number,
                        "records": len(bid_chunk),
                        "time_seconds": round(chunk_end - chunk_start, 3),
                    }
                )

        end_time = time()
        total_time = round(end_time - start_time, 3)
        avg_chunk_time = (
            round(sum(c["time_seconds"] for c in chunk_times) / len(chunk_times), 3)
            if chunk_times
            else 0
        )

        logger.info(f"Completed bid revocation. Total bids updated: {total_updated}")

        return {
            "auction_id": auction_id,
            "bids_revoked": total_updated,
            "status": "success",
            "timing": {
                "total_time_seconds": total_time,
                "average_chunk_time_seconds": avg_chunk_time,
                "chunks_processed": chunk_number,
                "records_per_second": (
                    round(total_updated / total_time, 2) if total_time > 0 else 0
                ),
                "detailed_chunks": chunk_times,
                "started_at": datetime.fromtimestamp(start_time).isoformat(),
                "completed_at": datetime.fromtimestamp(end_time).isoformat(),
            },
        }

    except Auction.DoesNotExist:
        logger.error(f"Auction {auction_id} not found")
        end_time = time()
        return {
            "auction_id": auction_id,
            "bids_revoked": 0,
            "status": "error",
            "message": f"Auction {auction_id} not found",
            "timing": {
                "total_time_seconds": round(end_time - start_time, 3),
                "started_at": datetime.fromtimestamp(start_time).isoformat(),
                "completed_at": datetime.fromtimestamp(end_time).isoformat(),
            },
        }
    except Exception as e:
        logger.error(f"Error processing auction {auction_id}: {str(e)}")
        end_time = time()
        return {
            "auction_id": auction_id,
            "bids_revoked": 0,
            "status": "error",
            "message": str(e),
            "timing": {
                "total_time_seconds": round(end_time - start_time, 3),
                "started_at": datetime.fromtimestamp(start_time).isoformat(),
                "completed_at": datetime.fromtimestamp(end_time).isoformat(),
            },
        }
