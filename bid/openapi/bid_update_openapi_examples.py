from drf_spectacular.openapi import OpenApiExample


def update_bid_examples():
    return [
        OpenApiExample(
            "Successful bid update (PATCH)",
            summary="Update an existing bid (Pending or Approved)",
            description="This example demonstrates a successful request to update a bid that"
            " is in a pending state or an approved bid with a reduced offer.",
            value={
                "offer": "1200.00",
            },
            request_only=True,
            status_codes=[200],
        ),
        OpenApiExample(
            "Successful bid update response (PATCH)",
            summary="Response for successfully Updating an existing bid (Pending or Approved)",
            description="This example demonstrates a successful response after updating a bid that"
            " is in a pending state or an approved bid with a reduced offer.",
            value={
                "id": "56fde4e4-85ae-4c11-b420-cc74a7d9d685",
                "author": "89180d7c-7a8e-4e7a-8133-f10313912fc4",
                "author_nickname": "AngryMaxwell455",
                "author_avatar": "https://api.dicebear.com/9.x/micah/svg?seed=826",
                "author_kyc_verified": False,
                "auction": "c39b607f-1c83-4bc5-a079-73b830bc6987",
                "auction_name": "High-Performance Laptop",
                "offer": "₾1200.00",
                "description": "Very descriptive description for an auction.",
                "delivery_fee": "₾25.00",
                "status": "Pending",
                "is_top_bid": True,
                "images": [
                    "https://reversello-bid-images.s3.amazonaws.com/bid_images/20f58f67-02c4-474f-"
                    "80f4-3e2a06df27d3-image_1",
                    "https://reversello-bid-images.s3.amazonaws.com/bid_images/20f58f67-02c4-474f-"
                    "80f4-3e2a06df27d3-image_2",
                ],
            },
            response_only=True,
            status_codes=[200],
        ),
        OpenApiExample(
            "Unauthorized user trying to update bid (PATCH)",
            summary="Unauthorized user",
            description="This example shows an unauthorized user trying to update a bid without authentication.",
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
            "to update a bid that does not belong to them.",
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
        OpenApiExample(
            "Error: Cannot increase offer for approved bid (PATCH)",
            summary="Error when trying to increase offer for an approved bid",
            description="This example shows an error response when a user tries to increase the offer "
            "of an approved bid. Only offer reductions are allowed for approved bids.",
            value={
                "type": "validation_error",
                "errors": [
                    {
                        "code": "invalid",
                        "message": "For approved bids, the offer can only be reduced.",
                        "field_name": "offer",
                    }
                ],
            },
            response_only=True,
            status_codes=[400],
        ),
        OpenApiExample(
            "Error: Rejected bids cannot be updated (PATCH)",
            summary="Attempt to update a rejected bid",
            description="This example shows an error response when a user "
            "tries to update a bid that has been rejected.",
            value={
                "type": "validation_error",
                "errors": [
                    {
                        "code": "invalid",
                        "message": "Rejected bids cannot be updated.",
                        "field_name": None,
                    }
                ],
            },
            response_only=True,
            status_codes=[400],
        ),
        OpenApiExample(
            "Error: Only the offer can be changed for approved bids (PATCH)",
            summary="Attempt to change fields other than the offer for an approved bid",
            description="This example shows an error response when a user tries to "
            "update fields other than the offer for an approved bid.",
            value={
                "type": "validation_error",
                "errors": [
                    {
                        "code": "invalid",
                        "message": "For approved bids, only the offer can be changed.",
                        "field_name": None,
                    }
                ],
            },
            response_only=True,
            status_codes=[400],
        ),
    ]
