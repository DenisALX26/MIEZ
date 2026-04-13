import logging
from typing import Any

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import exception_handler as drf_exception_handler

logger = logging.getLogger("django.request")


def _extract_field_errors(data: Any) -> dict[str, Any]:
    if isinstance(data, dict):
        field_errors: dict[str, Any] = {}
        for key, value in data.items():
            if key in {"detail", "code"}:
                continue
            field_errors[key] = value
        return field_errors

    return {}


def custom_exception_handler(exc, context):
    response = drf_exception_handler(exc, context)

    if response is None:
        logger.exception("Unhandled server exception", exc_info=exc)
        return Response(
            {
                "detail": "Internal server error.",
                "code": "server_error",
                "field_errors": {},
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    detail = response.data.get("detail", "Request failed.") if isinstance(response.data, dict) else "Request failed."
    code = "error"

    if hasattr(exc, "default_code"):
        code = getattr(exc, "default_code") or "error"

    field_errors = _extract_field_errors(response.data)

    response.data = {
        "detail": detail,
        "code": code,
        "field_errors": field_errors,
    }

    if response.status_code >= 500:
        logger.error("Server exception response generated", extra={"status_code": response.status_code})

    return response
