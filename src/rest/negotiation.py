"""PROJECT SARATHI REST Response Serialization & Content Negotiation."""

from __future__ import annotations

import json
from typing import Any

from src.http import Response
from .exceptions import ProblemDetails


class ContentNegotiator:
    """Content negotiation and response serializer."""

    @staticmethod
    def serialize(data: Any, accept_header: str = "application/json") -> Response:
        if isinstance(data, Response):
            return data

        if isinstance(data, ProblemDetails):
            return Response(
                json.dumps(data.to_dict()),
                status=data.status,
                media_type="application/problem+json",
            )

        if isinstance(data, (dict, list, int, float, bool)) or data is None:
            return Response(
                json.dumps(data),
                status=200,
                media_type="application/json",
            )

        if isinstance(data, str):
            return Response(data, status=200, media_type="text/plain; charset=utf-8")

        if hasattr(data, "to_dict") and callable(data.to_dict):
            return Response(
                json.dumps(data.to_dict()),
                status=200,
                media_type="application/json",
            )

        return Response(json.dumps(str(data)), status=200, media_type="application/json")
