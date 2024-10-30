from drf_spectacular.openapi import OpenApiExample


def examples():
    return [
        OpenApiExample(
            "Request example (POST)",
            summary="Create an auction",
            description="This example demonstrates how to create an auction with valid values.",
            value={
                "auction_name": "High-Performance Laptop",
                "description": "Laptop that performs good.",
                "category": "Electronics",
                "start_date": "2024-11-28 12:34:56.789012+00:00",
                "end_date": "2024-11-29 12:34:56.789012+00:00",
                "max_price": "1300.00",
                "quantity": 1,
                "accepted_bidders": "Individual",
                "accepted_locations": ["GE", "US"],
                "tags": [{"name": "Modern"}],
                "currency": "GEL",
                "custom_fields": {
                    "brand": "Asus",
                    "model": "Something",
                    "year": 2024,
                },
                "condition": "New",
            },
            request_only=True,
        ),
        OpenApiExample(
            "Response example 1 (POST)",
            summary="Successfully created an auction",
            description="This example demonstrates the response that will be returned after auction has been "
            "created successfully.",
            value={
                "id": "7aab82e5-ce90-4291-9739-ffa27564d4d1",
                "author": "0a85c5dd-c896-4802-8fa6-426220c78cd9",
                "author_avatar": "https://api.dicebear.com/9.x/micah/svg?seed=830",
                "author_nickname": "NostalgicRide939",
                "author_kyc_verified": False,
                "auction_name": "High-Performance Laptop",
                "description": "Laptop that performs good.",
                "category": "Electronics",
                "start_date": "2024-10-08T12:34:56.789012Z",
                "end_date": "2024-10-09T12:34:56.789012Z",
                "max_price": "1300.00",
                "quantity": 1,
                "accepted_bidders": "Individual",
                "accepted_locations": ["Georgia", "United States of America"],
                "tags": ["Modern"],
                "status": "Draft",
                "currency": "GEL",
                "custom_fields": {"brand": "Asus", "model": "Something", "year": 2024},
                "condition": "New",
            },
            response_only=True,
            status_codes=[201],
        ),
        OpenApiExample(
            "Response example 2 (POST)",
            summary="Successfully created an auction but warning occurred with websockets",
            description="This example demonstrates the response that will be returned after auction has been "
            "created successfully but for some reason it failed to send notification to websocket.",
            value={
                "warning": "Some king of warning",
                "id": "7aab82e5-ce90-4291-9739-ffa27564d4d1",
                "author": "0a85c5dd-c896-4802-8fa6-426220c78cd9",
                "author_avatar": "https://api.dicebear.com/9.x/micah/svg?seed=830",
                "author_nickname": "NostalgicRide939",
                "author_kyc_verified": False,
                "auction_name": "High-Performance Laptop",
                "description": "Laptop that performs good.",
                "category": "Electronics",
                "start_date": "2024-10-08T12:34:56.789012Z",
                "end_date": "2024-10-09T12:34:56.789012Z",
                "max_price": "1300.00",
                "quantity": 1,
                "accepted_bidders": "Individual",
                "accepted_locations": ["Georgia", "United States of America"],
                "tags": ["Modern"],
                "status": "Draft",
                "currency": "GEL",
                "custom_fields": {"brand": "Asus", "model": "Something", "year": 2024},
                "condition": "New",
            },
            response_only=True,
            status_codes=[201],
        ),
        OpenApiExample(
            "Response example 2 (POST)",
            summary="Response for invalid data.",
            description="This example demonstrates what will be returned in case user sends "
            "invalid data(Not everything covered here).",
            value={
                "type": "validation_error",
                "errors": [
                    {
                        "code": "invalid",
                        "message": "Invalid is not a valid category.",
                        "field_name": "category",
                    },
                    {
                        "code": "invalid",
                        "message": "Max price must be greater than 0.",
                        "field_name": "max_price",
                    },
                    {
                        "code": "min_value",
                        "message": "Ensure this value is greater than or equal to 0.",
                        "field_name": "quantity",
                    },
                    {
                        "code": "invalid_choice",
                        "message": '"Someone" is not a valid choice.',
                        "field_name": "accepted_bidders",
                    },
                    {
                        "code": "invalid_choice",
                        "message": '"RUB" is not a valid choice.',
                        "field_name": "currency",
                    },
                    {
                        "code": "invalid_choice",
                        "message": '"Invalid" is not a valid choice.',
                        "field_name": "tags.0.name",
                    },
                ],
            },
            response_only=True,
            status_codes=[400],
        ),
        OpenApiExample(
            "Response example 3 (POST)",
            summary="Unauthenticated tries to create an auction.",
            description="This example demonstrates the response for a "
            "scenario where non authenticated  user tries to "
            "create auction.",
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
            summary="User has no permission to create an auction.",
            description="This example demonstrates the response for a scenario where user does not have a "
            "permission to create an auction.",
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
