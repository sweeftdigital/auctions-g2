from drf_spectacular.openapi import OpenApiExample


def seller_statistics_examples():
    return [
        OpenApiExample(
            "Successful bid creation (POST)",
            summary="Response for successfully fetching statistics",
            description="This example demonstrates a successful response after seller "
            "successfully fetches their statistics about bids.",
            value={
                "total_bids": 3000,
                "total_auctions_participated": 3000,
                "completed_auctions_participated": 2900,
                "auctions_won": 500,
                "live_auction_bids": 1800,
                "success_rate": 79.50,
            },
            response_only=True,
            status_codes=[200],
        ),
        OpenApiExample(
            "Unauthorized user trying to create bid (POST)",
            summary="Unauthorized user",
            description="This example shows an unauthorized user trying to create a "
            "bid without authentication.",
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
            "Error: No permission. (GET)",
            summary="No permission to view statistics.",
            description="This example shows an error response when a user tries "
            "to see statistics but they do not have a Seller type of user.",
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
    ]
