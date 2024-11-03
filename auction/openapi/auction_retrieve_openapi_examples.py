from drf_spectacular.openapi import OpenApiExample


def examples():
    """
    Provides request and response examples for the RetrieveAuctionView.

    Returns:
        List[OpenApiExample]: A list of request/response examples for the RetrieveAuctionView.
    """
    return [
        OpenApiExample(
            "Response example 1 (GET)",
            summary="Successful retrieval of a published auction",
            description="This example demonstrates the response for a successful fetch of a "
            "published auction by its ID.",
            value={
                "id": "f5b00c42-305c-49e8-af5e-262a0d1a64fa",
                "accepted_locations": ["Afghanistan"],
                "tags": ["Luxury"],
                "category": "Watches",
                "author": "0a85c5dd-c896-4802-8fa6-426220c78cd9",
                "author_avatar": "https://api.dicebear.com/9.x/micah/svg?seed=830",
                "author_nickname": "NostalgicRide939",
                "author_kyc_verified": False,
                "auction_name": "Vintage Luxury Watch",
                "description": "A rare and exquisite vintage luxury watch with intricate details and a rich history.",
                "start_date": "2024-10-08T12:34:56.789012Z",
                "end_date": "2024-10-09T12:34:56.789012Z",
                "max_price": "₾5897.48",
                "quantity": 1,
                "accepted_bidders": "Company",
                "status": "Live",
                "currency": "GEL",
                "custom_fields": {
                    "brand": "Rolex",
                    "model": "Daytona",
                    "year": 1965,
                },
                "condition": "New",
                "created_at": "2024-10-07T15:22:44.554181Z",
                "updated_at": "2024-10-07T15:22:44.554190Z",
                "statistics": {
                    "winner_bid": "€5000",
                    "winner_bid_author": "1as2as3-c896-4802-8fa6-426220c78cd9",
                    "winner_bid_id": "7ca1as98-c896-4802-8fa6-426220c78cd9",
                    "top_bid": "€5000",
                    "top_bid_author": "1as2as3-c896-4802-8fa6-426220c78cd9",
                    "top_bid_id": "7ca1as98-c896-4802-8fa6-426220c78cd9",
                    "views_count": 2000,
                    "total_bids_count": 259,
                    "bookmarks_count": 147,
                },
                "bookmark_id": "5df7gf12-c896-4802-8fa6-426220c78cd9",
                "bookmarked": True,
                "has_bid": False,
            },
            response_only=True,
            status_codes=[200],
        ),
        OpenApiExample(
            "Response example 2 (GET)",
            summary="Successful retrieval of a draft auction by its author",
            description="This example demonstrates the response for a successful fetch of a "
            "draft auction by its author.",
            value={
                "id": "f5b00c42-305c-49e8-af5e-262a0d1a64fa",
                "accepted_locations": ["Afghanistan"],
                "tags": ["Luxury"],
                "category": "Watches",
                "author": "0a85c5dd-c896-4802-8fa6-426220c78cd9",
                "author_avatar": "https://api.dicebear.com/9.x/micah/svg?seed=830",
                "author_nickname": "NostalgicRide939",
                "author_kyc_verified": False,
                "auction_name": "Vintage Luxury Watch",
                "description": "A rare and exquisite vintage luxury watch with intricate details and a rich history.",
                "start_date": "2024-10-08T12:34:56.789012Z",
                "end_date": "2024-10-09T12:34:56.789012Z",
                "max_price": "$5879.48",
                "quantity": 1,
                "accepted_bidders": "Company",
                "status": "Draft",
                "currency": "GEL",
                "custom_fields": {
                    "brand": "Rolex",
                    "model": "Daytona",
                    "year": 1965,
                },
                "condition": "New",
                "created_at": "2024-10-07T15:22:44.554181Z",
                "updated_at": "2024-10-07T15:22:44.554190Z",
            },
            response_only=True,
            status_codes=[200],
        ),
        OpenApiExample(
            "Response example 3 (GET)",
            summary="Unauthorized access attempt",
            description="This example demonstrates the response for a scenario where a "
            "non-authenticated user tries to retrieve auction.",
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
            "Response example 4 (GET)",
            summary="Access denied for unpublished auction (draft) by non-author or user with Seller type account",
            description="This example demonstrates the response for a scenario where "
            "a non-author user tries to access a draft auction or user with the Seller type account tries "
            "to retrieve auction.",
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
            "Response example 5 (GET)",
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
