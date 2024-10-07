from drf_spectacular.openapi import OpenApiExample


def examples():
    """
    Provides request and response examples for the CreateBookmarkView.

    Returns:
        List[OpenApiExample]: A list of request/response examples for the CreateBookmarkView.
    """
    return [
        OpenApiExample(
            "Successful bookmark creation (POST)",
            summary="Create a bookmark of an existing auction",
            description="This example demonstrates a successful request to bookmark an "
            "existing auction.",
            value={
                "bookmark_id": "123e4567-89ab-cdef-0123-456789abcdef",
                "user_id": "0a85c5dd-c896-4802-8fa6-426220c78cd9",
                "auction_id": "f5b00c42-305c-49e8-af5e-262a0d1a64fa",
            },
            response_only=True,
            status_codes=[201],
        ),
        OpenApiExample(
            "Response example 6 (POST)",
            summary="Unauthenticated tries to create a bookmark..",
            description="This example demonstrates the response for a "
            "scenario where non authenticated  user tries to "
            "create bookmark.",
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
            summary="Attempt to bookmark a non-existent auction",
            description="This example demonstrates an error response when a user tries to "
            "bookmark an auction that does not exist.",
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
            "Error: Duplicate bookmark (POST)",
            summary="Attempt to bookmark an already bookmarked auction",
            description="This example demonstrates an error response when a user tries to "
            "bookmark an auction that they have already bookmarked.",
            value={
                "type": "validation_error",
                "errors": [
                    {
                        "code": "invalid",
                        "message": "This auction is already bookmarked.",
                        "field_name": None,
                    }
                ],
            },
            response_only=True,
            status_codes=[400],
        ),
    ]
