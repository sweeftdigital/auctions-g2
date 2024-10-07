from rest_framework import status
from rest_framework.response import Response
from rest_framework.test import APIRequestFactory, APITestCase

from auction.renderers import CustomJSONRenderer


class CustomJSONRendererTests(APITestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.renderer = CustomJSONRenderer()

    def test_render_400_bad_request(self):
        response_data = {"detail": "Invalid request"}
        response = Response(response_data, status=status.HTTP_400_BAD_REQUEST)
        renderer_context = {"response": response}
        rendered_data = self.renderer.render(
            response_data, renderer_context=renderer_context
        )

        expected_data = {
            "type": "bad_request",
            "errors": [
                {"code": "bad_request", "message": "Invalid request", "field_name": None}
            ],
        }
        self.assertJSONEqual(rendered_data, expected_data)

    def test_render_404_not_found(self):
        response_data = {"detail": "Not found"}
        response = Response(response_data, status=status.HTTP_404_NOT_FOUND)
        renderer_context = {"response": response}
        rendered_data = self.renderer.render(
            response_data, renderer_context=renderer_context
        )

        expected_data = {
            "type": "not_found",
            "errors": [{"code": "not_found", "message": "Not found", "field_name": None}],
        }
        self.assertJSONEqual(rendered_data, expected_data)

    def test_render_500_internal_server_error(self):
        response_data = {"detail": "Server error"}
        response = Response(response_data, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        renderer_context = {"response": response}
        rendered_data = self.renderer.render(
            response_data, renderer_context=renderer_context
        )

        expected_data = {
            "type": "internal_server_error",
            "errors": [
                {
                    "code": "internal_server_error",
                    "message": "Server error",
                    "field_name": None,
                }
            ],
        }
        self.assertJSONEqual(rendered_data, expected_data)

    def test_render_with_custom_errors(self):
        response_data = {"field_error": "This field is required."}
        response = Response(response_data, status=status.HTTP_400_BAD_REQUEST)
        renderer_context = {"response": response}
        rendered_data = self.renderer.render(
            response_data, renderer_context=renderer_context
        )

        expected_data = {
            "type": "bad_request",
            "errors": [
                {
                    "code": "bad_request",
                    "message": "This field is required.",
                    "field_name": None,
                }
            ],
        }
        self.assertJSONEqual(rendered_data, expected_data)

    def test_render_with_multiple_errors(self):
        response_data = {"field_1": "Error for field 1.", "field_2": "Error for field 2."}
        response = Response(response_data, status=status.HTTP_400_BAD_REQUEST)
        renderer_context = {"response": response}
        rendered_data = self.renderer.render(
            response_data, renderer_context=renderer_context
        )

        expected_data = {
            "type": "bad_request",
            "errors": [
                {
                    "code": "bad_request",
                    "message": "Error for field 1.",
                    "field_name": None,
                },
                {
                    "code": "bad_request",
                    "message": "Error for field 2.",
                    "field_name": None,
                },
            ],
        }
        self.assertJSONEqual(rendered_data, expected_data)
