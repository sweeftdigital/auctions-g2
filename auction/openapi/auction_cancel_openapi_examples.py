from drf_spectacular.openapi import OpenApiExample


def examples():
    return [
        OpenApiExample(
            "Successful auction cancellation (POST)",
            summary="Response for successfully cancelling auction",
            description="This example demonstrates a successful response after buyer "
            "successfully cancels their auction.",
            value={"message": "Auction was successfully canceled."},
            response_only=True,
            status_codes=[200],
        ),
        OpenApiExample(
            "Unauthorized user trying to cancel auction (POST)",
            summary="Unauthorized user",
            description="This example shows an unauthorized user trying to cancel an "
            "auction without authentication.",
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
            summary="No permission to cancel auction.",
            description="This example shows an error response when a user tries "
            "to cancel an auction that does not belong to them.",
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
