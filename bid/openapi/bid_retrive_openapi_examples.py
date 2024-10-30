from drf_spectacular.utils import OpenApiExample


def retrieve_bid_examples():
    return [
        OpenApiExample(
            "Successful bid retrieval (GET)",
            summary="Retrieve an existing bid",
            description="This example demonstrates a successful request to retrieve a bid.",
            value={
                "id": "9f275616-3b9a-4c21-b0d4-a9418a7983e4",
                "author": "e7f4b1f6-a759-4489-82ef-28fd5ff1d085",
                "author_avatar": "https://api.dicebear.com/9.x/micah/svg?seed=777",
                "author_nickname": "SadWozniak777",
                "author_kyc_verified": True,
                "auction": "39bdccae-3506-4e18-951a-9fdfa1228a22",
                "auction_name": "hp-Laptop",
                "offer": "€2800",
                "description": "string",
                "delivery_fee": "€122",
                "status": "Pending",
                "images": [
                    "https://hips.hearstapps.com/hmg-prod/images/2025-lexus-rx350-premium-101-"
                    "66f2dbe526c80.jpg?crop=0.788xw:0.666xh;0.0224xw,0.329xh&resize=2048:*"
                ],
            },
            response_only=True,
            status_codes=[200],
        ),
        OpenApiExample(
            "Unauthorized user trying to retrieve bid (GET)",
            summary="Unauthorized user",
            description="This example shows an unauthorized user attempting to retrieve a bid.",
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
            "Error: No permission (GET)",
            summary="No permission to perform the requested operation.",
            description="This example shows an error response when a user tries "
            "to retrieve a bid that does not belong to them, or "
            "if they are an user with user_type of Buyer and the "
            "auction on which the bid is placed does not belong "
            "to them.",
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
            "Error: Bid not found (GET)",
            summary="Bid not found",
            description="This example shows an error response when a user tries to retrieve a bid that doesn't exist.",
            value={
                "type": "client_error",
                "errors": [
                    {
                        "code": "not_found",
                        "message": "Bid not found or you are not the author.",
                        "field_name": None,
                    }
                ],
            },
            response_only=True,
            status_codes=[404],
        ),
    ]
