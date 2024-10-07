from drf_standardized_errors.formatter import ExceptionFormatter
from drf_standardized_errors.types import ErrorResponse


class CustomExceptionFormatter(ExceptionFormatter):
    def format_error_response(self, error_response: ErrorResponse):
        if error_response is not None:
            if error_response.errors[0].code in ["precondition_failed"]:
                response = {
                    "type": error_response.type,
                    "errors": [
                        {
                            **{
                                error.attr: error.detail
                                for error in error_response.errors
                            },
                            "field_name": None,
                        }
                    ],
                }
                return response

        return {
            "type": error_response.type,
            "errors": [
                {
                    "code": error.code,
                    "message": error.detail,
                    "field_name": error.attr,
                }
                for error in error_response.errors
            ],
        }
