"""Focused tests for M31 Pack 3 server adapter and example."""

from __future__ import annotations

import asyncio

import pytest

from examples.http.basic_server import application
from src.http import (
    ServerAdapterUnavailableError,
    ServerConfiguration,
    UvicornServerAdapter,
)


def test_server_configuration_has_safe_development_defaults() -> None:
    configuration = ServerConfiguration()
    assert configuration.host == "127.0.0.1"
    assert configuration.port == 8000
    assert configuration.log_level == "info"


@pytest.mark.parametrize(
    ("settings", "message"),
    [
        ({"host": " "}, "host"),
        ({"port": 0}, "port"),
        ({"port": 65536}, "port"),
        ({"port": True}, "port"),
        ({"log_level": "verbose"}, "log level"),
        ({"log_level": 1}, "log level"),
    ],
)
def test_server_configuration_rejects_invalid_values(settings, message) -> None:
    with pytest.raises(ValueError, match=message):
        ServerConfiguration(**settings)


def test_adapter_passes_validated_settings_to_runner() -> None:
    calls: list[tuple[object, dict[str, object]]] = []

    def runner(app, **settings):
        calls.append((app, settings))

    configuration = ServerConfiguration(
        host=" 0.0.0.0 ", port=8080, log_level="DEBUG"
    )
    adapter = UvicornServerAdapter(configuration, runner=runner)
    adapter.run(application)

    assert calls == [
        (
            application,
            {"host": "0.0.0.0", "port": 8080, "log_level": "debug"},
        )
    ]


def test_adapter_rejects_invalid_runner_and_application() -> None:
    with pytest.raises(TypeError, match="runner"):
        UvicornServerAdapter(runner=object())  # type: ignore[arg-type]
    with pytest.raises(TypeError, match="application"):
        UvicornServerAdapter(runner=lambda *args, **kwargs: None).run(object())  # type: ignore[arg-type]


def test_adapter_reports_missing_optional_server(monkeypatch) -> None:
    def missing(name: str):
        raise ModuleNotFoundError(name)

    monkeypatch.setattr("src.http.server.import_module", missing)
    with pytest.raises(ServerAdapterUnavailableError, match="not installed"):
        UvicornServerAdapter().run(application)


def test_basic_server_example_is_a_runnable_asgi_application() -> None:
    sent: list[dict[str, object]] = []

    async def receive() -> dict[str, object]:
        return {"type": "http.request", "body": b""}

    async def send(message: dict[str, object]) -> None:
        sent.append(message)

    asyncio.run(
        application(
            {
                "type": "http",
                "method": "GET",
                "path": "/health",
                "query_string": b"",
                "headers": [],
            },
            receive,
            send,
        )
    )
    assert sent[0]["status"] == 200
    assert sent[1]["body"] == b"PROJECT SARATHI is ready: GET /health"
