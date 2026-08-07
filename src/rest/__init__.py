"""PROJECT SARATHI REST Framework primitives."""

from .binding import FromBody, FromHeader, FromPath, FromQuery, FromServices
from .decorators import controller, delete, get, patch, post, put
from .exceptions import ProblemDetails, RestValidationError

__all__ = [
    "FromBody",
    "FromHeader",
    "FromPath",
    "FromQuery",
    "FromServices",
    "ProblemDetails",
    "RestValidationError",
    "controller",
    "delete",
    "get",
    "patch",
    "post",
    "put",
]

from .negotiation import ContentNegotiator
from .openapi import OpenApiGenerator
from .router import RestControllerRouter
