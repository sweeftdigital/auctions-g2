from drf_spectacular.openapi import OpenApiExample


def examples():
    """
    Provides request and response examples for the BookmarkListView.

    Returns:
        List[OpenApiExample]: A list of request/response examples for the BookmarkListView.
    """
    return [
        OpenApiExample(
            "Response example 1 (GET)",
            summary="Successful fetch of user's bookmarks (paginated)",
            description="This example demonstrates the response for a successful fetch of all the "
            "bookmarks created by the authenticated user. This response is paginated.",
            value={
                "id": "b2663154-ddbd-470e-a0a0-eec81dec0201",
                "user_id": "c3774265-ddbd-470e-a0a0-eec81dec0201",
                "auction": {
                    "id": "5624773c-ddbd-470e-a0a0-eec81dec0201",
                    "product": "High-Performance Laptop",
                    "status": "Upcoming",
                    "category": {"name": "Electronics"},
                    "max_price": "2000.00",
                    "currency": "USD",
                    "quantity": 5,
                    "start_date": "2024-10-08T12:34:56.789012Z",
                    "end_date": "2024-10-09T12:34:56.789012Z",
                },
            },
            response_only=True,
            status_codes=[200],
        ),
        OpenApiExample(
            "Response example 2 (GET)",
            summary="Empty response when user has no bookmarks",
            description="This example demonstrates the response for a scenario when the "
            "user has not bookmarked any auctions.",
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
            "Response example 3 (GET)",
            summary="Unauthorized access attempt",
            description="This example demonstrates the response for a scenario where a "
            "non-authenticated user tries to list bookmarks.",
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
