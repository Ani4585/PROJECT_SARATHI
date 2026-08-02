"""Deterministic synchronous and asynchronous hook dispatch."""

from __future__ import annotations

import inspect
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from time import monotonic
from typing import TypeAlias

from .model import (
    HookDecision,
    HookEvent,
    HookExecutionEvent,
    HookOutcome,
    HookReport,
    HookStatus,
)


HookReturn: TypeAlias = HookDecision | None
HookHandler: TypeAlias = Callable[[HookEvent], HookReturn | Awaitable[HookReturn]]
HookFilter: TypeAlias = Callable[[HookEvent], bool | Awaitable[bool]]
HookObserver: TypeAlias = Callable[[HookExecutionEvent], None]


@dataclass(frozen=True, slots=True)
class HookRegistration:
    hook: str
    owner: str
    handler: HookHandler
    priority: int = 0
    predicate: HookFilter | None = None


class HookRegistry:
    def __init__(
        self,
        *,
        clock: Callable[[], float] = monotonic,
        observer: HookObserver | None = None,
    ) -> None:
        self._registrations: dict[str, dict[str, HookRegistration]] = {}
        self._clock = clock
        self._observer = observer

    def register(
        self,
        hook: str,
        handler: HookHandler,
        *,
        owner: str,
        priority: int = 0,
        predicate: HookFilter | None = None,
    ) -> HookRegistration:
        hook = hook.strip()
        owner = owner.strip()
        if not hook or not owner:
            raise ValueError("Hook and owner names must not be blank.")
        if not callable(handler):
            raise TypeError("Hook handler must be callable.")
        if predicate is not None and not callable(predicate):
            raise TypeError("Hook filter must be callable.")
        if not isinstance(priority, int) or isinstance(priority, bool):
            raise TypeError("Hook priority must be an integer.")
        registrations = self._registrations.setdefault(hook, {})
        if owner in registrations:
            raise ValueError(f"Hook owner {owner!r} already registered for {hook!r}.")
        registration = HookRegistration(hook, owner, handler, priority, predicate)
        registrations[owner] = registration
        return registration

    def unregister(self, hook: str, owner: str) -> bool:
        registrations = self._registrations.get(hook)
        if registrations is None or owner not in registrations:
            return False
        del registrations[owner]
        if not registrations:
            del self._registrations[hook]
        return True

    def registrations(self, hook: str) -> tuple[HookRegistration, ...]:
        return tuple(
            sorted(
                self._registrations.get(hook, {}).values(),
                key=lambda item: (-item.priority, item.owner),
            )
        )

    def dispatch(self, event: HookEvent) -> HookReport:
        outcomes: list[HookOutcome] = []
        cancelled = False
        for registration in self.registrations(event.name):
            started = self._clock()
            try:
                if registration.predicate is not None:
                    selected = registration.predicate(event)
                    if inspect.isawaitable(selected):
                        if inspect.iscoroutine(selected):
                            selected.close()
                        raise TypeError("Async hook filter requires dispatch_async().")
                    if not selected:
                        outcome = self._outcome(registration, HookStatus.SKIPPED, started)
                        outcomes.append(outcome)
                        self._observe(event, outcome)
                        continue
                decision = registration.handler(event)
                if inspect.isawaitable(decision):
                    if inspect.iscoroutine(decision):
                        decision.close()
                    raise TypeError("Async hook handler requires dispatch_async().")
                status = HookStatus.CANCELLED if decision is HookDecision.CANCEL else HookStatus.SUCCEEDED
                outcome = self._outcome(registration, status, started)
                outcomes.append(outcome)
                self._observe(event, outcome)
                if decision is HookDecision.CANCEL:
                    cancelled = True
                    break
            except Exception as error:
                outcome = self._outcome(
                    registration,
                    HookStatus.FAILED,
                    started,
                    f"{type(error).__name__}: {error}",
                )
                outcomes.append(outcome)
                self._observe(event, outcome)
        return HookReport(event, tuple(outcomes), cancelled)

    async def dispatch_async(self, event: HookEvent) -> HookReport:
        outcomes: list[HookOutcome] = []
        cancelled = False
        for registration in self.registrations(event.name):
            started = self._clock()
            try:
                if registration.predicate is not None:
                    selected = registration.predicate(event)
                    if inspect.isawaitable(selected):
                        selected = await selected
                    if not selected:
                        outcome = self._outcome(registration, HookStatus.SKIPPED, started)
                        outcomes.append(outcome)
                        self._observe(event, outcome)
                        continue
                decision = registration.handler(event)
                if inspect.isawaitable(decision):
                    decision = await decision
                status = HookStatus.CANCELLED if decision is HookDecision.CANCEL else HookStatus.SUCCEEDED
                outcome = self._outcome(registration, status, started)
                outcomes.append(outcome)
                self._observe(event, outcome)
                if decision is HookDecision.CANCEL:
                    cancelled = True
                    break
            except Exception as error:
                outcome = self._outcome(
                    registration,
                    HookStatus.FAILED,
                    started,
                    f"{type(error).__name__}: {error}",
                )
                outcomes.append(outcome)
                self._observe(event, outcome)
        return HookReport(event, tuple(outcomes), cancelled)

    def _outcome(
        self,
        registration: HookRegistration,
        status: HookStatus,
        started: float,
        message: str | None = None,
    ) -> HookOutcome:
        return HookOutcome(
            registration.owner,
            status,
            max(0.0, self._clock() - started),
            message,
        )

    def _observe(self, event: HookEvent, outcome: HookOutcome) -> None:
        if self._observer is None:
            return
        try:
            self._observer(
                HookExecutionEvent(
                    event.name,
                    outcome.owner,
                    outcome.status,
                    outcome.duration_seconds,
                )
            )
        except Exception:
            pass
