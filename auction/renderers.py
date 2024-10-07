from rest_framework.renderers import JSONRenderer


class CustomJSONRenderer(JSONRenderer):
    RESPONSE_TYPES = {
        400: "bad_request",
        401: "unauthorized",
        403: "forbidden",
        404: "not_found",
        405: "method_not_allowed",
        406: "not_acceptable",
        408: "timeout",
        409: "conflict",
        429: "too_many_requests",
        503: "service_unavailable",
        500: "internal_server_error",
    }

    def render(self, data, accepted_media_type=None, renderer_context=None):
        if renderer_context:
            response = renderer_context.get("response")
            if response:
                if self.is_error_response(response):
                    return self.process_error_response(
                        data, response, accepted_media_type, renderer_context
                    )

        return super().render(data, accepted_media_type, renderer_context)

    def is_error_response(self, response):
        return response.status_code >= 400

    def process_error_response(
        self, data, response, accepted_media_type, renderer_context
    ):
        response_data = {
            "type": self.RESPONSE_TYPES.get(response.status_code, "unknown"),
            "errors": [],
        }

        if "errors" in data:
            return super().render(data, accepted_media_type, renderer_context)
        else:
            response_data["errors"] = [
                self.format_error(
                    {
                        "message": error,
                        "code": response_data["type"],
                    }
                )
                for error in data.values()
            ]

        return super().render(response_data, accepted_media_type, renderer_context)

    def format_error(self, error):
        return {
            "code": error.get("code", "unknown"),
            "message": error.get("message", "An error occurred."),
            "field_name": error.get("field_name", None),
        }
