from drf_spectacular.openapi import OpenApiExample


def examples():
    return [
        OpenApiExample(
            "Successful bid creation (POST)",
            summary="Response for successfully declaring winner",
            description="This example demonstrates a successful response after seller "
            "successfully fetches their statistics about bids.",
            value={
                "message": "Winner of this auction has successfully been declared",
                "bid_id": "e78b8009-231f-4c6d-82b5-960fbbed2fbf",
                "auction_id": "5cbcbf41-50e8-404c-b384-4a515d50cd97",
                "winner_offer": "₾500.00",
                "winner_author_id": "748f2e52-5d0b-4de2-a733-dedc41450eb7",
            },
            response_only=True,
            status_codes=[200],
        ),
        OpenApiExample(
            "Unauthorized user trying to declare winner (POST)",
            summary="Unauthorized user",
            description="This example shows an unauthorized user trying to declare a "
            "winner bid without authentication.",
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
            summary="No permission to declare winner.",
            description="This example shows an error response when a user tries "
            "to declare a winner but is not author of the auction or is not a Buyer type of user.",
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
