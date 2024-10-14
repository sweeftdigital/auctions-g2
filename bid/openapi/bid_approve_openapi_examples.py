from drf_spectacular.openapi import OpenApiExample


def approve_bid_examples():
    return [
        OpenApiExample(
            "Successful bid approval (POST)",
            summary="Approve an existing bid",
            description="This example demonstrates a successful request to approve an existing bid.",
            value=None,
            request_only=True,
            status_codes=[200],
        ),
        OpenApiExample(
            "Unauthorized user trying to approve bid (POST)",
            summary="Unauthorized user",
            description="This example shows an unauthorized user trying to approve a bid without authentication.",
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
            "Error: Bid not found or unauthorized (POST)",
            summary="Bid not found or unauthorized",
            description="This example shows an error response when a user tries to approve a bid that "
            "doesn't exist or doesn't belong to them.",
            value={
                "type": "client_error",
                "errors": [
                    {
                        "code": "not_found",
                        "message": "Bid not found or you are not the owner of this auction.",
                        "field_name": None,
                    }
                ],
            },
            response_only=True,
            status_codes=[404],
        ),
        OpenApiExample(
            "Error: Bid already approved (POST)",
            summary="Bid already approved",
            description="This example shows an error response when a user tries to approve a bid "
            "that has already been approved.",
            value={
                "type": "validation_error",
                "errors": [
                    {
                        "code": "invalid",
                        "message": "This bid has already been approved.",
                        "field_name": None,
                    }
                ],
            },
            response_only=True,
            status_codes=[400],
        ),
        OpenApiExample(
            "Error: User is not the auction owner (POST)",
            summary="User is not the auction owner",
            description="This example shows an error response when a user who is not the owner of the auction "
            "tries to approve a bid.",
            value={
                "type": "permission_denied",
                "errors": [
                    {
                        "code": "permission_denied",
                        "message": "You are not the owner of this auction.",
                        "field_name": None,
                    }
                ],
            },
            response_only=True,
            status_codes=[403],
        ),
    ]
