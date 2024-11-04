from drf_spectacular.openapi import OpenApiExample


def examples():
    return [
        OpenApiExample(
            "Successful auction leave (POST)",
            summary="Response for successfully leaving an auction",
            description="This example demonstrates a successful response after seller "
            "successfully leaves an auction.",
            value={
                "message": "Successfully left the auction",
                "user_id": "7ca1as98-c896-4802-8fa6-426220c78cd9",
                "cancelled_auction_count": 24,
            },
            response_only=True,
            status_codes=[200],
        ),
        OpenApiExample(
            "User trying to leave an auction with a status of Draft or Cancelled (POST)",
            summary="leaving an auction with a status of Draft or Cancelled",
            description="This example shows response for a scenario where "
            "user wants to send a request of leaving an auction with a status of "
            "Draft or Cancelled.",
            value={
                "type": "validation_error",
                "errors": [
                    {
                        "code": "invalid",
                        "message": "You can not leave an auction that has been cancelled, drafted.",
                        "field_name": None,
                    }
                ],
            },
            response_only=True,
            status_codes=[400],
        ),
        OpenApiExample(
            "Auction has not started yet (POST)",
            summary="Auction has not started yet",
            description="This example shows response for user that wants "
            "to leave an auction that has not started yet.",
            value={
                "type": "validation_error",
                "errors": [
                    {
                        "code": "invalid",
                        "message": "You can not leave an auction that has not started yet.",
                        "field_name": None,
                    }
                ],
            },
            response_only=True,
            status_codes=[400],
        ),
        OpenApiExample(
            "Auction has ended (POST)",
            summary="Auction has already ended",
            description="This example shows response for user that wants "
            "to leave an auction that has already ended.",
            value={
                "type": "validation_error",
                "errors": [
                    {
                        "code": "invalid",
                        "message": "You can not leave an auction that has already been completed.",
                        "field_name": None,
                    }
                ],
            },
            response_only=True,
            status_codes=[400],
        ),
        OpenApiExample(
            "User is a winner of an auction (POST)",
            summary="User is a winner of an auction",
            description="This example shows response for user that wants "
            "to leave an auction but is a winner of an auction.",
            value={
                "type": "validation_error",
                "errors": [
                    {
                        "code": "invalid",
                        "message": "As a winner of an auction, you can not leave it.",
                        "field_name": None,
                    }
                ],
            },
            response_only=True,
            status_codes=[400],
        ),
        OpenApiExample(
            "Unauthorized user trying to leave an auction (POST)",
            summary="Unauthorized user",
            description="This example shows an unauthorized user trying to leave an "
            "auction without authentication.",
            value={
                "type": "client_error",
                "errors": [
                    {
                        "code": "not_authenticated",
                        "message": "Authentication credentials were not provided.",
                        "field_name": None,
                    }
                ],
            },
            response_only=True,
            status_codes=[401],
        ),
        OpenApiExample(
            "Error: No permission. (POST)",
            summary="No permission to leave an auction.",
            description="This example shows an error response when a user tries "
            "to leave an auction but they do not have permission(e.g they are Buyer "
            "type of user.",
            value={
                "type": "client_error",
                "errors": [
                    {
                        "code": "permission_denied",
                        "message": "You do not have permission to perform this action.",
                        "field_name": None,
                    }
                ],
            },
            response_only=True,
            status_codes=[403],
        ),
        OpenApiExample(
            "Response example 5 (POST)",
            summary="Auction not found",
            description="This example demonstrates the response for a scenario where "
            "the requested auction ID does not exist.",
            value={
                "type": "client_error",
                "errors": [
                    {"code": "not_found", "message": "Not found.", "field_name": None}
                ],
            },
            response_only=True,
            status_codes=[404],
        ),
        OpenApiExample(
            "Response example 6 (POST)",
            summary="Active bids not found",
            description="This example demonstrates the response for a scenario where "
            "the user wants to leave an auction but they do not have no "
            "active bids created on that auction.",
            value={
                "type": "not_found",
                "errors": [
                    {
                        "code": "not_found",
                        "message": "No active bids found for this auction",
                        "field_name": None,
                    }
                ],
            },
            response_only=True,
            status_codes=[404],
        ),
    ]
