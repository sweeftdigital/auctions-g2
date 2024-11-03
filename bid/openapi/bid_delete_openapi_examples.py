from drf_spectacular.openapi import OpenApiExample


def delete_bid_examples():
    return [
        OpenApiExample(
            "Successful bid delete response (DELETE)",
            summary="Response for successfully deleting a bid",
            description="This example demonstrates a successful response after deleting a bid.",
            value={},
            response_only=True,
            status_codes=[204],
        ),
        OpenApiExample(
            "Unauthorized user trying to delete bid (DELETE)",
            summary="Unauthorized user",
            description="This example shows an unauthorized user trying to delete a bid without authentication.",
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
            "to delete a bid that does not belong to them.",
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
            "Error: Bid not found or unauthorized (PATCH)",
            summary="Bid not found or unauthorized",
            description="This example shows an error response when a user tries to update a bid that"
            " doesn't exist or doesn't belong to them.",
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
