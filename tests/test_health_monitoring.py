"""Tests for official M14 operational health monitoring."""

from __future__ import annotations

import json
import time
from argparse import Namespace
from pathlib import Path

import pytest

from scripts.tooling.cli.commands.monitor import MonitorCommand
from scripts.tooling.cli.context import CommandContext
from src.health import (
    HealthCheck,
    HealthCheckRegistry,
    HealthGroup,
    HealthJsonRenderer,
    HealthResult,
    HealthRunner,
    HealthStatus,
    HealthTextRenderer,
    create_default_health_registry,
)


class FakeCheck(HealthCheck):
    def __init__(
        self,
        name: str,
        *,
        group: HealthGroup = HealthGroup.READINESS,
        status: HealthStatus = HealthStatus.HEALTHY,
        dependencies: tuple[str, ...] = (),
        critical: bool = True,
        timeout: float = 1.0,
        action=None,
    ) -> None:
        self._name = name
        self._group = group
        self._status = status
        self._dependencies = dependencies
        self._critical = critical
        self._timeout = timeout
        self._action = action

    @property
    def name(self) -> str:
        return self._name

    @property
    def group(self) -> HealthGroup:
        return self._group

    @property
    def critical(self) -> bool:
        return self._critical

    @property
    def dependencies(self) -> tuple[str, ...]:
        return self._dependencies

    @property
    def timeout_seconds(self) -> float:
        return self._timeout

    def run(self) -> HealthResult:
        if self._action:
            self._action()
        return HealthResult(self.name, self.group, self._status, "Completed.")


def registry_with(*checks: HealthCheck) -> HealthCheckRegistry:
    registry = HealthCheckRegistry()
    for check in checks:
        registry.register(check)
    return registry


def test_registry_rejects_duplicate_and_invalid_timeout() -> None:
    registry = registry_with(FakeCheck("check"))
    with pytest.raises(ValueError):
        registry.register(FakeCheck("check"))
    with pytest.raises(ValueError):
        HealthCheckRegistry().register(FakeCheck("timeout", timeout=0))


def test_runner_honors_dependency_order() -> None:
    calls: list[str] = []
    first = FakeCheck("first", action=lambda: calls.append("first"))
    second = FakeCheck("second", dependencies=("first",), action=lambda: calls.append("second"))
    report = HealthRunner(registry_with(second, first)).run((HealthGroup.READINESS,))
    assert calls == ["first", "second"]
    assert tuple(result.name for result in report.results) == ("first", "second")
    assert report.status is HealthStatus.HEALTHY


def test_runner_skips_check_with_unhealthy_dependency() -> None:
    report = HealthRunner(
        registry_with(
            FakeCheck("first", status=HealthStatus.UNHEALTHY),
            FakeCheck("second", dependencies=("first",)),
        )
    ).run((HealthGroup.READINESS,))
    assert report.results[1].status is HealthStatus.SKIPPED
    assert "Blocked by: first" in report.results[1].details


def test_critical_failure_is_unhealthy_but_noncritical_failure_is_degraded() -> None:
    critical = HealthRunner(registry_with(FakeCheck("critical", status=HealthStatus.UNHEALTHY))).run()
    optional = HealthRunner(
        registry_with(FakeCheck("optional", status=HealthStatus.UNHEALTHY, critical=False))
    ).run()
    assert critical.status is HealthStatus.UNHEALTHY
    assert critical.passed is False
    assert optional.status is HealthStatus.DEGRADED
    assert optional.passed is True


def test_runner_isolates_exception() -> None:
    def broken() -> None:
        raise RuntimeError("boom")

    report = HealthRunner(registry_with(FakeCheck("broken", action=broken))).run()
    assert report.results[0].status is HealthStatus.UNHEALTHY
    assert report.results[0].details == ("RuntimeError: boom",)


def test_runner_enforces_timeout() -> None:
    report = HealthRunner(
        registry_with(FakeCheck("slow", timeout=0.001, action=lambda: time.sleep(0.03)))
    ).run()
    assert report.results[0].status is HealthStatus.UNHEALTHY
    assert "exceeded its timeout" in report.results[0].summary


def test_runner_rejects_missing_dependency_and_cycle() -> None:
    with pytest.raises(ValueError, match="unavailable dependencies"):
        HealthRunner(registry_with(FakeCheck("check", dependencies=("missing",)))).run()
    with pytest.raises(ValueError, match="cycle"):
        HealthRunner(
            registry_with(
                FakeCheck("first", dependencies=("second",)),
                FakeCheck("second", dependencies=("first",)),
            )
        ).run()


def prepare_project(root: Path) -> None:
    for name in ("src", "config", "docs"):
        (root / name).mkdir()
    (root / "config" / "settings.py").write_text("VALUE = 1\n", encoding="utf-8")


def test_default_registry_runs_all_health_groups(tmp_path: Path) -> None:
    prepare_project(tmp_path)
    report = HealthRunner(create_default_health_registry(tmp_path)).run()
    assert report.status is HealthStatus.HEALTHY
    assert tuple(result.group for result in report.results) == (
        HealthGroup.LIVENESS,
        HealthGroup.READINESS,
        HealthGroup.READINESS,
        HealthGroup.STARTUP,
        HealthGroup.STARTUP,
    )


def test_health_renderers_are_machine_and_human_readable() -> None:
    report = HealthRunner(registry_with(FakeCheck("check"))).run()
    assert "[HEALTHY] check" in HealthTextRenderer().render(report)
    document = json.loads(HealthJsonRenderer().render(report))
    assert document["summary"]["status"] == "healthy"


def test_monitor_command_supports_group_filter(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    prepare_project(tmp_path)
    exit_code = MonitorCommand().execute(
        CommandContext(tmp_path, "python"),
        Namespace(group="liveness", format="json"),
    )
    document = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert document["summary"]["groups"] == ["liveness"]
    assert document["summary"]["checks"] == 1
