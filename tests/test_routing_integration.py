"""Focused tests for M32 Pack 3 grouping, reversal, and HTTP dispatch."""

from __future__ import annotations

import asyncio

import pytest

from src.http import HttpApplication, Response, TextResponse
from src.routing import (
    InvalidRouteError,
    ReverseRouteError,
    RouteGroup,
    Router,
    RoutingHandler,
)


def handler(request, **parameters):
    return TextResponse(str(parameters))


def http_scope(path: str, method: str = "GET") -> dict[str, object]:
    return {
        "type": "http",
        "method": method,
        "path": path,
        "query_string": b"",
        "headers": [],
    }


async def dispatch(application, path: str, method: str = "GET"):
    sent: list[dict[str, object]] = []

    async def receive():
        return {"type": "http.request", "body": b""}

    async def send(message):
        sent.append(message)

    await application(http_scope(path, method), receive, send)
    return sent


def test_reverse_static_and_typed_routes() -> None:
    router = Router()
    router.add("/health", handler, name="health")
    router.add("/users/{user_id:int}", handler, name="users.detail")
    assert router.url_path_for("health") == "/health"
    assert router.url_path_for("users.detail", user_id=42) == "/users/42"


def test_reverse_routes_encode_segments_and_preserve_path_remainders() -> None:
    router = Router()
    router.add("/search/{term}", handler, name="search")
    router.add("/files/{location:path}", handler, name="files")
    assert router.url_path_for("search", term="circular economy") == (
        "/search/circular%20economy"
    )
    assert router.url_path_for("files", location="docs/start here") == (
        "/files/docs/start%20here"
    )


def test_reverse_routes_reject_missing_extra_and_unknown_values() -> None:
    router = Router()
    router.add("/users/{user_id:int}", handler, name="user")
    with pytest.raises(ReverseRouteError, match="missing"):
        router.url_path_for("user")
    with pytest.raises(ReverseRouteError, match="extra"):
        router.url_path_for("user", user_id=1, other=2)
    with pytest.raises(ReverseRouteError, match="Unknown"):
        router.url_path_for("missing")


def test_group_prefix_and_name_prefix_are_applied() -> None:
    group = RouteGroup("/users", name_prefix="users.")
    group.add("/", handler, name="list")
    group.add("/{user_id:int}", handler, name="detail")
    router = Router()
    routes = router.include(group, prefix="/api/v1", name_prefix="public.")
    assert [route.path for route in routes] == [
        "/api/v1/users",
        "/api/v1/users/{user_id:int}",
    ]
    assert router.url_path_for("public.users.detail", user_id=7) == (
        "/api/v1/users/7"
    )


def test_group_decorator_returns_original_handler() -> None:
    group = RouteGroup("/reports")

    @group.route("/daily", name="daily")
    def daily(request):
        return Response("daily")

    router = Router()
    router.include(group)
    assert router.get("daily").handler is daily


@pytest.mark.parametrize("prefix", ["relative", "/trailing/", "/double//path"])
def test_group_rejects_invalid_prefixes(prefix: str) -> None:
    with pytest.raises(InvalidRouteError):
        RouteGroup(prefix)


def test_router_include_validates_group_type() -> None:
    with pytest.raises(TypeError, match="RouteGroup"):
        Router().include(object())  # type: ignore[arg-type]


def test_sync_route_handler_dispatches_through_http_application() -> None:
    router = Router()
    router.add(
        "/hello/{name}",
        lambda request, name: TextResponse(f"Hello {name}"),
    )
    messages = asyncio.run(dispatch(HttpApplication(router.handler()), "/hello/Sarathi"))
    assert messages[0]["status"] == 200
    assert messages[1]["body"] == b"Hello Sarathi"


def test_async_route_handler_receives_typed_parameters() -> None:
    async def detail(request, item_id):
        return TextResponse(f"item={item_id}:{type(item_id).__name__}")

    router = Router()
    router.add("/items/{item_id:int}", detail)
    messages = asyncio.run(dispatch(HttpApplication(router.handler()), "/items/9"))
    assert messages[1]["body"] == b"item=9:int"


def test_http_dispatch_returns_plain_404_response() -> None:
    application = HttpApplication(Router().handler())
    messages = asyncio.run(dispatch(application, "/missing"))
    assert messages[0]["status"] == 404
    assert messages[1]["body"] == b"Not Found"


def test_http_dispatch_returns_405_and_allow_header() -> None:
    router = Router()
    router.add("/items", handler, methods=("POST", "GET"))
    messages = asyncio.run(dispatch(HttpApplication(router.handler()), "/items", "DELETE"))
    assert messages[0]["status"] == 405
    assert (b"allow", b"GET, POST") in messages[0]["headers"]
    assert messages[1]["body"] == b"Method Not Allowed"


def test_routing_handler_requires_router() -> None:
    with pytest.raises(TypeError, match="Router"):
        RoutingHandler(object())  # type: ignore[arg-type]


def test_group_conflicts_are_checked_by_target_router() -> None:
    group = RouteGroup("/users")
    group.add("/{first}", handler)
    group.add("/{second}", handler)
    with pytest.raises(Exception, match="Ambiguous"):
        Router().include(group)
