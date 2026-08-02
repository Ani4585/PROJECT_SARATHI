"""Focused tests for M32 Pack 2 router resolution."""

from __future__ import annotations

import pytest

from src.routing import (
    ConverterRegistry,
    InvalidRouteError,
    MethodNotAllowedError,
    Route,
    RouteConflictError,
    RouteNotFoundError,
    Router,
)


def first(request):
    return request


def second(request):
    return request


def test_router_adds_and_resolves_named_route() -> None:
    router = Router()
    route = router.add("/users/{user_id:int}", first, name="users.detail")
    match = router.resolve("/users/42", "get")
    assert match.route is route
    assert match.parameters["user_id"] == 42
    assert router.get("users.detail") is route
    assert router.routes == (route,)


def test_static_route_wins_independent_of_registration_order() -> None:
    for dynamic_first in (True, False):
        router = Router()
        routes = [
            ("/users/{username}", first, "dynamic"),
            ("/users/current", second, "static"),
        ]
        if not dynamic_first:
            routes.reverse()
        for path, handler, name in routes:
            router.add(path, handler, name=name)
        assert router.resolve("/users/current", "GET").route.name == "static"


def test_typed_route_wins_over_generic_string_route() -> None:
    router = Router()
    router.add("/items/{value}", first, name="string")
    router.add("/items/{value:int}", second, name="integer")
    assert router.resolve("/items/12", "GET").route.name == "integer"
    assert router.resolve("/items/code", "GET").route.name == "string"


def test_segment_route_wins_over_catch_all_route() -> None:
    router = Router()
    router.add("/files/{location:path}", first, name="catch_all")
    router.add("/files/{folder}/{name}", second, name="two_segments")
    assert router.resolve("/files/docs/index", "GET").route.name == "two_segments"


def test_missing_path_raises_explicit_404_error() -> None:
    router = Router()
    router.add("/known", first)
    with pytest.raises(RouteNotFoundError) as captured:
        router.resolve("/missing", "GET")
    assert captured.value.status_code == 404
    assert captured.value.path == "/missing"


def test_wrong_method_raises_405_with_sorted_allowed_methods() -> None:
    router = Router()
    router.add("/items", first, methods=("POST", "GET"))
    with pytest.raises(MethodNotAllowedError) as captured:
        router.resolve("/items", "DELETE")
    assert captured.value.status_code == 405
    assert captured.value.allowed_methods == ("GET", "POST")


def test_match_returns_none_without_hiding_invalid_methods() -> None:
    router = Router()
    router.add("/items", first)
    assert router.match("/missing", "GET") is None
    assert router.match("/items", "POST") is None
    with pytest.raises(InvalidRouteError, match="method"):
        router.match("/items", "bad method")


def test_allowed_methods_combines_disjoint_routes() -> None:
    router = Router()
    router.add("/items", first, methods=("GET",))
    router.add("/items", second, methods=("POST",))
    assert router.allowed_methods("/items") == ("GET", "POST")
    assert router.allowed_methods("/missing") == ()
    assert router.resolve("/items", "POST").route.handler is second


def test_overlapping_same_shape_routes_are_rejected() -> None:
    router = Router()
    router.add("/users/{first_name}", first, methods=("GET", "POST"))
    with pytest.raises(RouteConflictError, match="Ambiguous"):
        router.add("/users/{second_name}", second, methods=("GET",))


def test_duplicate_names_are_rejected_even_for_distinct_paths() -> None:
    router = Router()
    router.add("/one", first, name="duplicate")
    with pytest.raises(RouteConflictError, match="name"):
        router.add("/two", second, name="duplicate")


def test_register_requires_route_instance() -> None:
    with pytest.raises(TypeError, match="Route"):
        Router().register(object())  # type: ignore[arg-type]


def test_route_decorator_registers_and_returns_original_handler() -> None:
    router = Router()

    @router.route("/decorated", methods=("PUT",), name="decorated")
    def decorated(request):
        return request

    assert router.get("decorated").handler is decorated
    assert router.resolve("/decorated", "PUT").route.handler is decorated


def test_router_uses_shared_custom_converter_registry() -> None:
    class Code:
        regex = r"[A-Z]{2}"
        weight = 40

        def parse(self, value: str) -> object:
            return value.lower()

        def format(self, value: object) -> str:
            return str(value).upper()

    converters = ConverterRegistry.defaults()
    converters.register("code", Code())
    router = Router(converters=converters)
    router.add("/regions/{region:code}", first)
    assert router.resolve("/regions/IN", "GET").parameters["region"] == "in"


def test_external_route_can_be_registered() -> None:
    route = Route("/external", first, name="external")
    router = Router()
    router.register(route)
    assert router.get("external") is route


def test_unknown_route_name_raises_not_found() -> None:
    with pytest.raises(RouteNotFoundError, match="missing"):
        Router().get("missing")
