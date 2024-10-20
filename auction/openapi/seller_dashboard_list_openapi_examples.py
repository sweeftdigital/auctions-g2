from drf_spectacular.openapi import OpenApiExample


def examples():
    """
    Provides request and response examples for the SellerAuctionListView.

    Returns:
        List[OpenApiExample]: A list of request/response examples for the SellerAuctionListView.
    """
    return [
        OpenApiExample(
            "Response example 1 (GET)",
            summary="Successful fetch of seller's auctions",
            description="This example demonstrates the response for a successful fetch of all "
            "seller's auctions.",
            value={
                "id": "2ea3de7f-944b-44d6-919f-519130b7d583",
                "author": "0a85c5dd-c896-4802-8fa6-426220c78cd9",
                "product": "Strawberry",
                "status": "Upcoming",
                "category": {"name": "Food & Beverages"},
                "max_price": "€15000.00",
                "currency": "EUR",
                "quantity": 1000,
                "start_date": "2024-10-08T12:34:56.789012Z",
                "end_date": "2024-10-08T12:34:57.789012Z",
                "tags": ["fruit", "food"],
            },
            response_only=True,
            status_codes=[200],
        ),
        OpenApiExample(
            "Response example 2 (GET)",
            summary="Empty response when fetching seller's auctions",
            description="This example demonstrates the response for a scenario when the "
            "seller has no auctions created.",
            response_only=True,
            status_codes=[200],
            value={
                "count": 0,
                "next": None,
                "previous": None,
                "results": [],
            },
        ),
        OpenApiExample(
            "Response example 3 (POST)",
            summary="Unauthenticated tries to access seller's dashboard.",
            description="This example demonstrates the response for a scenario where a "
            "non-authenticated user tries to list auctions.",
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
            "Response example 4 (POST)",
            summary="Non-seller tries to access seller's dashboard.",
            description="This example demonstrates the response for a scenario where a non-seller "
            "type of user tries to list auctions.",
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
            summary="Passing invalid page query parameter.",
            description="This example demonstrates the response for passing"
            "invalid query param like 0 or `string`.",
            value={
                "type": "client_error",
                "errors": [
                    {"code": "not_found", "message": "Invalid page.", "field_name": None}
                ],
            },
            response_only=True,
            status_codes=[404],
        ),
    ]
