from drf_spectacular.utils import OpenApiExample


def list_bid_examples():
    return [
        OpenApiExample(
            "Successful bid retrieval for all bids (GET)",
            summary="List all bids of a user",
            description="This example demonstrates a successful request to list bids on particular auction.",
            value={
                "id": "9f275616-3b9a-4c21-b0d4-a9418a7983e4",
                "author": "e7f4b1f6-a759-4489-82ef-28fd5ff1d085",
                "author_avatar": "https://api.dicebear.com/9.x/micah/svg?seed=777",
                "author_nickname": "SadWozniak777",
                "author_kyc_verified": True,
                "auction": "39bdccae-3506-4e18-951a-9fdfa1228a22",
                "auction_status": "Live",
                "auction_author_nickname": "QuirkyMclaren241",
                "auction_max_price": "₾1300.00",
                "offer": "$2800",
                "description": "string",
                "delivery_fee": "$122",
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
            "Successful bid retrieval for specified auction (GET)",
            summary="List existing bids on auction",
            description="This example demonstrates a successful request to list bids on particular auction.",
            value={
                "user_bids": [
                    {
                        "id": "e4597a56-c4ce-497f-8193-84638e367764",
                        "author": "748f2e52-5d0b-4de2-a733-dedc41450eb7",
                        "author_nickname": "GoofyChaum240'",
                        "author_avatar": "https://api.dicebear.com/9.x/micah/svg?seed=826",
                        "author_kyc_verified": False,
                        "auction": "5e10d49b-bf3a-4ecb-b845-ed2a51551cb1",
                        "offer": "₾30.00",
                        "description": "Placing my bid for this auction",
                        "delivery_fee": "₾25.00",
                        "status": "Pending",
                        "images": [
                            "https://hips.hearstapps.com/hmg-prod/images/2025-lexus-rx350-premium-101-"
                            "66f2dbe526c80.jpg?crop=0.788xw:0.666xh;0.0224xw,0.329xh&resize=2048:*",
                        ],
                    },
                    {
                        "id": "fee07951-7a63-4b95-8335-06a65ae47f75",
                        "author": "748f2e52-5d0b-4de2-a733-dedc41450eb7",
                        "author_nickname": "GoofyChaum240",
                        "author_avatar": "https://api.dicebear.com/9.x/micah/svg?seed=826",
                        "author_kyc_verified": False,
                        "auction": "5e10d49b-bf3a-4ecb-b845-ed2a51551cb1",
                        "offer": "₾500.00",
                        "description": "Placing my bid for this auction",
                        "delivery_fee": "₾25.00",
                        "status": "Pending",
                        "images": [],
                    },
                ],
                "top_bids": [
                    {
                        "id": "e4597a56-c4ce-497f-8193-84638e367764",
                        "author": "748f2e52-5d0b-4de2-a733-dedc41450eb7",
                        "author_nickname": "GoofyChaum240",
                        "author_avatar": "https://api.dicebear.com/9.x/micah/svg?seed=826",
                        "author_kyc_verified": False,
                        "auction": "5e10d49b-bf3a-4ecb-b845-ed2a51551cb1",
                        "offer": "₾30.00",
                        "description": "Placing my bid for this auction",
                        "delivery_fee": "₾25.00",
                        "status": "Pending",
                        "images": [
                            "https://hips.hearstapps.com/hmg-prod/images/2025-lexus-rx350-premium-101-"
                            "66f2dbe526c80.jpg?crop=0.788xw:0.666xh;0.0224xw,0.329xh&resize=2048:*",
                        ],
                    },
                    {
                        "id": "748f2e52-9f63-4cad-8564-b1d9558cd103",
                        "author": "2b791267-5d0b-4de2-a733-dedc41450eb7",
                        "author_nickname": "SadWozniak988",
                        "author_avatar": "https://api.dicebear.com/9.x/micah/svg?seed=756",
                        "author_kyc_verified": False,
                        "auction": "5e10d49b-bf3a-4ecb-b845-ed2a51551cb1",
                        "offer": "₾31.00",
                        "description": "Placing my bid for this auction",
                        "delivery_fee": "₾25.00",
                        "status": "Pending",
                        "images": [
                            "https://hips.hearstapps.com/hmg-prod/images/2025-lexus-rx350-premium-101-"
                            "66f2dbe526c80.jpg?crop=0.788xw:0.666xh;0.0224xw,0.329xh&resize=2048:*",
                            "https://hips.hearstapps.com/hmg-prod/images/2025-lexus-rx350-premium-101-"
                            "66f2dbe526c80.jpg?crop=0.788xw:0.666xh;0.0224xw,0.329xh&resize=2048:*",
                            "https://hips.hearstapps.com/hmg-prod/images/2025-lexus-rx350-premium-101-"
                            "66f2dbe526c80.jpg?crop=0.788xw:0.666xh;0.0224xw,0.329xh&resize=2048:*",
                        ],
                    },
                    {
                        "id": "C2002cbf-f9e3-4479-be64-65f1f429b6e5",
                        "author": "5e10d49b-5d0b-4de2-a733-dedc41450eb7",
                        "author_nickname": "HappyTesla777",
                        "author_avatar": "https://api.dicebear.com/9.x/micah/svg?seed=777",
                        "author_kyc_verified": False,
                        "auction": "5e10d49b-bf3a-4ecb-b845-ed2a51551cb1",
                        "offer": "₾32.00",
                        "description": "Placing my bid for this auction",
                        "delivery_fee": "₾25.00",
                        "status": "Pending",
                        "images": [
                            "https://hips.hearstapps.com/hmg-prod/images/2025-lexus-rx350-premium-101-"
                            "66f2dbe526c80.jpg?crop=0.788xw:0.666xh;0.0224xw,0.329xh&resize=2048:*",
                            "https://hips.hearstapps.com/hmg-prod/images/2025-lexus-rx350-premium-101-"
                            "66f2dbe526c80.jpg?crop=0.788xw:0.666xh;0.0224xw,0.329xh&resize=2048:*",
                            "https://hips.hearstapps.com/hmg-prod/images/2025-lexus-rx350-premium-101-"
                            "66f2dbe526c80.jpg?crop=0.788xw:0.666xh;0.0224xw,0.329xh&resize=2048:*",
                            "https://hips.hearstapps.com/hmg-prod/images/2025-lexus-rx350-premium-101-"
                            "66f2dbe526c80.jpg?crop=0.788xw:0.666xh;0.0224xw,0.329xh&resize=2048:*",
                            "https://hips.hearstapps.com/hmg-prod/images/2025-lexus-rx350-premium-101-"
                            "66f2dbe526c80.jpg?crop=0.788xw:0.666xh;0.0224xw,0.329xh&resize=2048:*",
                        ],
                    },
                ],
            },
            response_only=True,
            status_codes=[200],
        ),
        OpenApiExample(
            "Unauthorized user trying to list bids (GET)",
            summary="Unauthorized user",
            description="This example shows an unauthorized user attempting to list bids.",
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
            "User with no permission to list bids (GET)",
            summary="User has no permission to access this endpoint.",
            description="This example demonstrates the response for a scenario where user does not have a "
            "permission to access this endpoint, this may occur when seller tries to access an "
            "endpoint made for buyer type of user or buyer tries to access endpoint made for seller "
            "type of users..",
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
            "Auction could not be found (GET)",
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
    ]
