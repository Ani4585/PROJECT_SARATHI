"""Tests for the M20 integrated platform kernel."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime

import pytest

from src.application.messaging import Query
from src.domain.events import DomainEvent
from src.jobs import Job, JobStatus
from src.kernel import PlatformKernel, PlatformKernelBuilder
from src.modules import BaseModule, ModuleRuntimeState, ModuleStartupError


@dataclass(frozen=True, slots=True, kw_only=True)
class Ping(Query):
    value: str


@dataclass(frozen=True, slots=True, kw_only=True)
class Pinged(DomainEvent):
    value: str


class RecordingModule(BaseModule):
    name = "recording"

    def __init__(self, calls: list[str], fail: bool = False) -> None:
        self.calls = calls
        self.fail = fail

    def configure(self, container: object) -> None:
        self.calls.append("configure")

    def start(self, context: object) -> None:
        self.calls.append("start")
        if self.fail:
            raise RuntimeError("boom")

    def stop(self, context: object) -> None:
        self.calls.append("stop")


def test_builder_registers_integrated_services() -> None:
    kernel = PlatformKernelBuilder().build()
    assert kernel.container.resolve("kernel") is kernel
    assert kernel.container.resolve("events") is kernel.events
    assert kernel.container.resolve("messages") is kernel.messages
    assert kernel.container.resolve("modules") is kernel.modules
    assert kernel.container.resolve("jobs") is kernel.jobs
    assert kernel.container.resolve("metrics") is kernel.metrics
    assert kernel.container.resolve_type(PlatformKernel) is kernel


def test_builder_configures_modules_before_returning_kernel() -> None:
    calls: list[str] = []
    kernel = PlatformKernelBuilder().add_module(RecordingModule(calls)).build()
    assert calls == ["configure"]
    assert kernel.modules.state is ModuleRuntimeState.CONFIGURED


def test_kernel_starts_and_stops_module_runtime() -> None:
    calls: list[str] = []
    kernel = PlatformKernelBuilder().add_module(RecordingModule(calls)).build()
    kernel.start()
    assert kernel.running is True
    kernel.stop()
    assert kernel.running is False
    assert calls == ["configure", "start", "stop"]


def test_kernel_health_exposes_release_and_runtime_state() -> None:
    kernel = PlatformKernelBuilder().build()
    health = kernel.health()
    assert health.framework == "PROJECT SARATHI"
    assert health.version == "0.8.19"
    assert health.milestone == "M32"
    assert health.state == "STOPPED"


def test_kernel_guards_runtime_operations_until_started() -> None:
    kernel = PlatformKernelBuilder().build()
    with pytest.raises(RuntimeError, match="not running"):
        kernel.send(Ping(value="hello"))
    with pytest.raises(RuntimeError, match="not running"):
        kernel.publish(Pinged(value="hello"))
    with pytest.raises(RuntimeError, match="not running"):
        kernel.run_jobs()


def test_kernel_dispatches_messages_and_records_metrics() -> None:
    kernel = PlatformKernelBuilder().build()
    kernel.messages.register_query(Ping, lambda query: query.value.upper())
    kernel.start()
    assert kernel.send(Ping(value="hello")) == "HELLO"
    assert kernel.metrics.snapshot().find("kernel.messages.sent").value == 1.0  # type: ignore[union-attr]
    kernel.stop()


def test_kernel_publishes_events_and_records_handler_failures() -> None:
    kernel = PlatformKernelBuilder().build()
    kernel.events.subscribe(Pinged, lambda event: (_ for _ in ()).throw(RuntimeError("boom")))
    kernel.start()
    report = kernel.publish(Pinged(value="hello"))
    assert report.succeeded is False
    assert kernel.metrics.snapshot().find("kernel.events.published").value == 1.0  # type: ignore[union-attr]
    assert kernel.metrics.snapshot().find("kernel.events.handler_failures").value == 1.0  # type: ignore[union-attr]
    kernel.stop()


def test_kernel_executes_scheduled_jobs_and_records_metrics() -> None:
    kernel = PlatformKernelBuilder().build()
    kernel.jobs.schedule(Job("job", lambda: 42, datetime.now(UTC)))
    kernel.start()
    executions = kernel.run_jobs()
    assert executions[0].status is JobStatus.SUCCEEDED
    assert executions[0].result == 42
    assert kernel.metrics.snapshot().find("kernel.jobs.executed").value == 1.0  # type: ignore[union-attr]
    kernel.stop()


def test_kernel_marks_lifecycle_failed_when_module_start_fails() -> None:
    kernel = PlatformKernelBuilder().add_module(RecordingModule([], fail=True)).build()
    with pytest.raises(ModuleStartupError):
        kernel.start()
    assert kernel.lifecycle.get_state() == "FAILED"
    assert kernel.metrics.snapshot().find("kernel.start.failures").value == 1.0  # type: ignore[union-attr]


def test_kernel_rejects_duplicate_start_and_stop_when_inactive() -> None:
    kernel = PlatformKernelBuilder().build()
    with pytest.raises(RuntimeError):
        kernel.stop()
    kernel.start()
    with pytest.raises(RuntimeError):
        kernel.start()
    kernel.stop()
