from drf_spectacular.openapi import OpenApiExample


def examples():
    """
    Provides request and response examples for the RetrieveAuctionView.

    Returns:
        List[OpenApiExample]: A list of request/response examples for the RetrieveAuctionView.
    """
    return [
        OpenApiExample(
            "Response example 2 (POST)",
            summary="Successful delete of an auction by its author",
            description="This example demonstrates the response for a successful delete of an "
            "auction by its author.",
            value={},
            response_only=True,
            status_codes=[204],
        ),
        OpenApiExample(
            "Response example 3 (POST)",
            summary="Unauthorized access attempt",
            description="This example demonstrates the response for a scenario where a "
            "non-authenticated user tries to delete an auction.",
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
            summary="User does not have permissions to delete auction",
            description="This example demonstrates the response for a scenario where "
            "a non-author user tries to delete an auction or user with user type of Seller"
            "tried to delete the auction.",
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
    ]
