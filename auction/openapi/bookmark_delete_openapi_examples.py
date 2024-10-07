from drf_spectacular.openapi import OpenApiExample


def examples():
    """
    Provides request and response examples for the DeleteBookmarkView.

    Returns:
        List[OpenApiExample]: A list of request/response examples for the DeleteBookmarkView.
    """
    return [
        OpenApiExample(
            "Successful bookmark deletion (DELETE)",
            summary="Delete an existing bookmark",
            description="This example demonstrates a successful request to delete an existing bookmark.",
            response_only=True,
            status_codes=[204],
        ),
        OpenApiExample(
            "Error: Bookmark not found (DELETE)",
            summary="Attempt to delete a non-existent bookmark",
            description="This example demonstrates an error response when a user tries to "
            "delete a bookmark that does not exist.",
            value={
                "type": "client_error",
                "errors": [
                    {"code": "not_found", "message": "Invalid page.", "field_name": None}
                ],
            },
            response_only=True,
            status_codes=[404],
        ),
        OpenApiExample(
            "Error: Unauthorized access (DELETE)",
            summary="Unauthenticated user attempts to delete a bookmark",
            description="This example demonstrates an error response when an unauthenticated "
            "user tries to delete a bookmark.",
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
            "Error: Permission denied (DELETE)",
            summary="Non-owner tries to delete a bookmark",
            description="This example demonstrates an error response when a user tries to delete "
            "a bookmark they do not own.",
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
