"""Focused tests for M32 Pack 1 route models and converters."""

from __future__ import annotations

from uuid import UUID

import pytest

from src.routing import (
    ConverterRegistry,
    InvalidRouteError,
    ParameterConversionError,
    Route,
    UnknownConverterError,
)


def handler(request):
    return request


def test_static_route_matches_exact_path_and_normalized_method() -> None:
    route = Route("/health", handler, methods=("get",), name="health")
    match = route.match("/health", "GET")
    assert match is not None
    assert match.route is route
    assert match.method == "GET"
    assert dict(match.parameters) == {}
    assert route.match("/health/", "GET") is None
    assert route.match("/health", "POST") is None


def test_default_string_parameter_matches_one_segment() -> None:
    route = Route("/users/{username}", handler)
    match = route.match("/users/sarathi", "get")
    assert match is not None
    assert match.parameters == {"username": "sarathi"}
    assert route.match("/users/a/b", "GET") is None


def test_integer_parameter_is_converted_and_rejects_non_digits() -> None:
    route = Route("/users/{user_id:int}", handler)
    match = route.match("/users/42", "GET")
    assert match is not None
    assert match.parameters["user_id"] == 42
    assert route.match("/users/-1", "GET") is None
    assert route.match("/users/nope", "GET") is None


def test_uuid_parameter_returns_uuid_value() -> None:
    route = Route("/items/{item_id:uuid}", handler)
    match = route.match("/items/123e4567-e89b-12d3-a456-426614174000", "GET")
    assert match is not None
    assert match.parameters["item_id"] == UUID(
        "123e4567-e89b-12d3-a456-426614174000"
    )


def test_path_remainder_captures_multiple_segments() -> None:
    route = Route("/files/{location:path}", handler)
    match = route.match("/files/docs/guide/index.html", "GET")
    assert match is not None
    assert match.parameters["location"] == "docs/guide/index.html"


def test_root_route_is_supported() -> None:
    route = Route("/", handler)
    assert route.match("/", "GET") is not None
    assert route.match("", "GET") is None


@pytest.mark.parametrize(
    "path",
    ["relative", "/trailing/", "/double//segment", "/query?x=1", "/part-{id}"],
)
def test_invalid_route_paths_are_rejected(path: str) -> None:
    with pytest.raises(InvalidRouteError):
        Route(path, handler)


def test_duplicate_parameters_and_nonfinal_remainders_are_rejected() -> None:
    with pytest.raises(InvalidRouteError, match="Duplicate"):
        Route("/{value}/{value}", handler)
    with pytest.raises(InvalidRouteError, match="final"):
        Route("/{rest:path}/tail", handler)


def test_unknown_converter_and_invalid_name_are_rejected() -> None:
    with pytest.raises(UnknownConverterError, match="missing"):
        Route("/{value:missing}", handler)
    with pytest.raises(InvalidRouteError, match="name"):
        Route("/valid", handler, name="not a name")


def test_methods_are_validated_normalized_and_deduplicated() -> None:
    route = Route("/items", handler, methods=("get", "POST"))
    assert route.methods == ("GET", "POST")
    with pytest.raises(InvalidRouteError, match="Duplicate"):
        Route("/items", handler, methods=("GET", "get"))
    with pytest.raises(InvalidRouteError, match="non-empty"):
        Route("/items", handler, methods=())


def test_handler_must_be_callable() -> None:
    with pytest.raises(TypeError, match="handler"):
        Route("/items", object())  # type: ignore[arg-type]


def test_converter_registry_accepts_custom_converter() -> None:
    class Slug:
        regex = r"[a-z]+(?:-[a-z]+)*"
        weight = 25

        def parse(self, value: str) -> object:
            return value.upper()

        def format(self, value: object) -> str:
            return str(value).lower()

    registry = ConverterRegistry.defaults()
    registry.register("slug", Slug())
    route = Route("/posts/{slug:slug}", handler, converters=registry)
    assert route.match("/posts/project-sarathi", "GET").parameters == {  # type: ignore[union-attr]
        "slug": "PROJECT-SARATHI"
    }


def test_converter_registry_rejects_duplicates_and_invalid_contracts() -> None:
    registry = ConverterRegistry.defaults()
    with pytest.raises(ValueError, match="already"):
        registry.register("str", registry.get("str"))
    with pytest.raises(TypeError, match="contract"):
        registry.register("broken", object())  # type: ignore[arg-type]


def test_converter_formatters_validate_reverse_values() -> None:
    registry = ConverterRegistry.defaults()
    assert registry.get("int").format(12) == "12"
    assert registry.get("uuid").format(
        "123e4567-e89b-12d3-a456-426614174000"
    ) == "123e4567-e89b-12d3-a456-426614174000"
    assert registry.get("path").format("/docs/start/") == "docs/start"
    with pytest.raises(ParameterConversionError):
        registry.get("str").format("two/segments")
