"""Integrated PROJECT SARATHI platform kernel."""

from __future__ import annotations

from src.application.messaging import Message, MessageBus
from src.container import ServiceContainer
from src.core.version import FRAMEWORK_NAME, MILESTONE, VERSION
from src.domain.events import DomainEvent, EventBus, PublicationReport
from src.jobs import JobExecution, JobScheduler
from src.lifecycle import LifecycleManager
from src.metrics import MetricsRegistry
from src.modules import ModuleRuntime, ModuleRuntimeState

from .health import KernelHealth


class PlatformKernel:
    """Coordinate framework services through one guarded runtime boundary."""

    def __init__(
        self,
        *,
        container: ServiceContainer,
        lifecycle: LifecycleManager,
        events: EventBus,
        messages: MessageBus,
        modules: ModuleRuntime,
        jobs: JobScheduler,
        metrics: MetricsRegistry,
    ) -> None:
        self.container = container
        self.lifecycle = lifecycle
        self.events = events
        self.messages = messages
        self.modules = modules
        self.jobs = jobs
        self.metrics = metrics

    @property
    def running(self) -> bool:
        return self.lifecycle.get_state() == "RUNNING"

    def start(self) -> None:
        if self.running:
            raise RuntimeError("Platform kernel is already running.")
        self.lifecycle.start()
        try:
            self.modules.start(self)
        except Exception:
            self.lifecycle.fail()
            self.metrics.increment("kernel.start.failures")
            raise
        self.lifecycle.mark_running()
        self.metrics.set_gauge("kernel.running", 1)
        self.metrics.increment("kernel.starts")

    def stop(self) -> None:
        self._require_running()
        try:
            self.modules.stop(self)
        finally:
            self.lifecycle.stop()
            self.metrics.set_gauge("kernel.running", 0)
            self.metrics.increment("kernel.stops")

    def publish(self, event: DomainEvent) -> PublicationReport:
        self._require_running()
        with self.metrics.timer(
            "kernel.event.duration",
            {"event": type(event).__name__},
        ):
            report = self.events.publish(event)
        self.metrics.increment("kernel.events.published")
        if not report.succeeded:
            self.metrics.increment("kernel.events.handler_failures", report.failed_handlers)
        return report

    def send(self, message: Message) -> object:
        self._require_running()
        with self.metrics.timer(
            "kernel.message.duration",
            {"message": type(message).__name__},
        ):
            result = self.messages.send(message)
        self.metrics.increment("kernel.messages.sent")
        return result

    def run_jobs(self) -> tuple[JobExecution, ...]:
        self._require_running()
        with self.metrics.timer("kernel.jobs.duration"):
            executions = self.jobs.run_due()
        self.metrics.increment("kernel.jobs.executed", len(executions))
        failures = sum(execution.error is not None for execution in executions)
        if failures:
            self.metrics.increment("kernel.jobs.failures", failures)
        return executions

    def health(self) -> KernelHealth:
        return KernelHealth(
            framework=FRAMEWORK_NAME,
            version=VERSION,
            milestone=MILESTONE,
            state=self.lifecycle.get_state(),
            modules=self.modules.plan,
            scheduled_jobs=len(self.jobs.records),
            metric_series=len(self.metrics.snapshot().samples),
        )

    def _require_running(self) -> None:
        if not self.running:
            raise RuntimeError("Platform kernel is not running.")
