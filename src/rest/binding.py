"""PROJECT SARATHI Typed Parameter Binding for REST Endpoints."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class FromQuery:
    name: str | None = None
    default: Any = None


@dataclass(frozen=True)
class FromPath:
    name: str | None = None


@dataclass(frozen=True)
class FromBody:
    required: bool = True


@dataclass(frozen=True)
class FromHeader:
    name: str | None = None
    default: Any = None


@dataclass(frozen=True)
class FromServices:
    service_type: type | None = None
