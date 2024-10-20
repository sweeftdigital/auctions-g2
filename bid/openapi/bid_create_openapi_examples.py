from drf_spectacular.openapi import OpenApiExample


def create_bid_examples():
    return [
        OpenApiExample(
            "Successful bid creation (POST)",
            summary="Create a bid for a live auction",
            description="This example demonstrates a successful request to create a bid for a live auction.",
            value={
                "offer": "500.0",
                "description": "Placing my bid for this auction",
                "delivery_fee": "25.0",
                "images": [
                    {"image_url": "https://example.com/image1.jpg"},
                    {"image_url": "https://example.com/image2.jpg"},
                ],
            },
            request_only=True,
            status_codes=[201],
        ),
        OpenApiExample(
            "Successful bid creation (POST)",
            summary="Response for successfully creating bid",
            description="This example demonstrates a successful response after creating a bid.",
            value={
                "id": "b6f0c9c7-deaa-4699-9e77-d26e5b4e1338",
                "author": "00dd3466-a745-41fe-b5f4-bb1818ec8dbf",
                "auction": "e890e8e7-91c5-4c2e-8a28-a2a522a3bcc9",
                "auction_name": "High-Performance Laptop",
                "offer": "₾500.00",
                "description": "Placing my bid for this auction",
                "delivery_fee": "₾25.00",
                "status": "Pending",
            },
            response_only=True,
            status_codes=[201],
        ),
        OpenApiExample(
            "Unauthorized user trying to create bid (POST)",
            summary="Unauthorized user",
            description="This example shows an unauthorized user trying to create a bid without authentication.",
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
            "Error: Auction does not exist (POST)",
            summary="Auction not found",
            description="This example shows an error response when a user "
            "tries to create a bid for an auction that does not exist.",
            value={
                "type": "validation_error",
                "errors": [
                    {
                        "code": "invalid",
                        "message": "Auction does not exist.",
                        "field_name": "auction",
                    }
                ],
            },
            response_only=True,
            status_codes=[404],
        ),
        OpenApiExample(
            "Error: More than one field provided or offer missing (PATCH)",
            summary="Invalid update payload: More than one field or no offer",
            description="This example shows an error response when a user attempts to "
            "update a bid but either provides multiple fields or omits the `offer` field.",
            value={
                "type": "validation_error",
                "errors": [
                    {
                        "code": "invalid",
                        "message": "Offer not provided or more than one field was provided.",
                        "field_name": "offer",
                    }
                ],
            },
            response_only=True,
            status_codes=[400],
        ),
        OpenApiExample(
            "Error: Auction is not live (POST)",
            summary="Cannot bid on auction that is not live",
            description="This example shows an error response when a user tries to bid"
            " on an auction that is not in the live state.",
            value={
                "type": "validation_error",
                "errors": [
                    {
                        "code": "invalid",
                        "message": "You can only bid on live auctions.",
                        "field_name": "auction_status",
                    }
                ],
            },
            response_only=True,
            status_codes=[400],
        ),
        OpenApiExample(
            "Error: User is not a seller (POST)",
            summary="User is not a seller",
            description="This example shows an error response when a non-seller tries to place a bid.",
            value={
                "type": "validation_error",
                "errors": [
                    {
                        "code": "invalid",
                        "message": "Only sellers can place bids.",
                        "field_name": "user_type",
                    }
                ],
            },
            response_only=True,
            status_codes=[400],
        ),
        OpenApiExample(
            "Error: Only companies can bid (POST)",
            summary="Only companies can bid on this auction",
            description="This example shows an error response when a user tries to create a bid for an "
            "auction that only allows companies to bid, and the user is not a company.",
            value={
                "type": "validation_error",
                "errors": [
                    {
                        "code": "invalid",
                        "message": "Only companies can bid on this auction.",
                        "field_name": "user_type",
                    }
                ],
            },
            response_only=True,
            status_codes=[400],
        ),
        OpenApiExample(
            "Error: Only individuals can bid (POST)",
            summary="Only individuals can bid on this auction",
            description="This example shows an error response when a user tries to create a bid for "
            "an auction that only allows individuals to bid, and the user is not an individual.",
            value={
                "type": "validation_error",
                "errors": [
                    {
                        "code": "invalid",
                        "message": "Only individuals can bid on this auction.",
                        "field_name": "user_type",
                    }
                ],
            },
            response_only=True,
            status_codes=[400],
        ),
    ]
