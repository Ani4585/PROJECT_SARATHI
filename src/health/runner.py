"""Dependency-aware, timeout-bounded operational health execution."""

from __future__ import annotations

from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeoutError
from dataclasses import replace
from time import perf_counter

from .check import HealthCheck
from .model import HealthGroup, HealthReport, HealthResult, HealthStatus
from .registry import HealthCheckRegistry


class HealthRunner:
    def __init__(self, registry: HealthCheckRegistry, clock: Callable[[], float] = perf_counter) -> None:
        self._registry = registry
        self._clock = clock

    def run(self, groups: tuple[HealthGroup, ...] | None = None) -> HealthReport:
        selected_groups = groups or tuple(HealthGroup)
        checks = self._ordered_checks(self._registry.checks(selected_groups))
        started = self._clock()
        results: dict[str, HealthResult] = {}
        for check in checks:
            blocked = tuple(
                dependency
                for dependency in check.dependencies
                if results[dependency].status is not HealthStatus.HEALTHY
            )
            if blocked:
                results[check.name] = HealthResult(
                    check.name,
                    check.group,
                    HealthStatus.SKIPPED,
                    "Health check skipped because a dependency is not healthy.",
                    critical=check.critical,
                    details=("Blocked by: " + ", ".join(blocked),),
                )
            else:
                results[check.name] = self._run_check(check)
        duration = max(0.0, self._clock() - started)
        return HealthReport(selected_groups, tuple(results[check.name] for check in checks), duration)

    def _ordered_checks(self, checks: tuple[HealthCheck, ...]) -> tuple[HealthCheck, ...]:
        by_name = {check.name: check for check in checks}
        for check in checks:
            missing = tuple(name for name in check.dependencies if name not in by_name)
            if missing:
                raise ValueError(f"Health check {check.name} has unavailable dependencies: {', '.join(missing)}")
        ordered: list[HealthCheck] = []
        visiting: set[str] = set()
        visited: set[str] = set()

        def visit(check: HealthCheck) -> None:
            if check.name in visiting:
                raise ValueError(f"Health check dependency cycle detected at {check.name}.")
            if check.name in visited:
                return
            visiting.add(check.name)
            for dependency in sorted(check.dependencies):
                visit(by_name[dependency])
            visiting.remove(check.name)
            visited.add(check.name)
            ordered.append(check)

        for check in checks:
            visit(check)
        return tuple(ordered)

    def _run_check(self, check: HealthCheck) -> HealthResult:
        started = self._clock()
        executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix=f"health-{check.name}")
        future = executor.submit(check.run)
        try:
            result = future.result(timeout=check.timeout_seconds)
            if not isinstance(result, HealthResult) or result.name != check.name or result.group is not check.group:
                raise TypeError("Health check returned an invalid or mismatched result.")
            return replace(
                result,
                duration_seconds=max(0.0, self._clock() - started),
                critical=check.critical,
            )
        except FutureTimeoutError:
            future.cancel()
            return HealthResult(
                check.name,
                check.group,
                HealthStatus.UNHEALTHY,
                "Health check exceeded its timeout.",
                max(0.0, self._clock() - started),
                check.critical,
                (f"Timeout: {check.timeout_seconds:.3f} seconds",),
            )
        except Exception as error:
            return HealthResult(
                check.name,
                check.group,
                HealthStatus.UNHEALTHY,
                "Health check raised an exception.",
                max(0.0, self._clock() - started),
                check.critical,
                (f"{type(error).__name__}: {error}",),
            )
        finally:
            executor.shutdown(wait=False, cancel_futures=True)
