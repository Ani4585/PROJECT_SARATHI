"""Route definitions and deterministic path matching."""

from __future__ import annotations

import re
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from types import MappingProxyType
from urllib.parse import quote

from .converters import ConverterRegistry, PathConverter
from .exceptions import InvalidRouteError, ParameterConversionError, ReverseRouteError


_PARAMETER = re.compile(
    r"^\{(?P<name>[A-Za-z_][A-Za-z0-9_]*)(?::(?P<converter>[A-Za-z_][A-Za-z0-9_]*))?\}$"
)
_PARAMETER_INLINE = re.compile(
    r"\{(?P<name>[A-Za-z_][A-Za-z0-9_]*)(?::(?P<converter>[A-Za-z_][A-Za-z0-9_]*))?\}"
)
_METHOD = re.compile(r"^[!#$%&'*+.^_`|~0-9A-Za-z-]+$")
_ROUTE_NAME = re.compile(r"^[A-Za-z_][A-Za-z0-9_.-]*$")


@dataclass(frozen=True, slots=True)
class RouteParameter:
    name: str
    converter_name: str
    converter: PathConverter


@dataclass(frozen=True, slots=True)
class RouteMatch:
    route: "Route"
    method: str
    parameters: Mapping[str, object]


class Route:
    """Validated route template compiled into an anchored matcher."""

    def __init__(
        self,
        path: str,
        handler: Callable[..., object],
        *,
        methods: Sequence[str] = ("GET",),
        name: str | None = None,
        converters: ConverterRegistry | None = None,
    ) -> None:
        if not callable(handler):
            raise TypeError("Route handler must be callable.")
        self.path = self._validate_path(path)
        self.methods = self._normalize_methods(methods)
        if name is not None and (
            not isinstance(name, str) or not _ROUTE_NAME.fullmatch(name)
        ):
            raise InvalidRouteError("Route name is invalid.")
        self.name = name
        self.handler = handler
        self._registry = converters or ConverterRegistry.defaults()
        pattern, parameters, precedence, signature = self._compile()
        self._pattern = re.compile(pattern)
        self.parameters = parameters
        self.precedence = precedence
        self.signature = signature

    @staticmethod
    def _validate_path(path: str) -> str:
        if not isinstance(path, str) or not path.startswith("/"):
            raise InvalidRouteError("Route path must be an absolute path.")
        if "?" in path or "#" in path:
            raise InvalidRouteError("Route path must not contain a query or fragment.")
        if path != "/" and (path.endswith("/") or "//" in path):
            raise InvalidRouteError("Route path contains an empty segment.")
        return path

    @staticmethod
    def _normalize_methods(methods: Sequence[str]) -> tuple[str, ...]:
        if isinstance(methods, str) or not methods:
            raise InvalidRouteError("Route methods must be a non-empty sequence.")
        normalized: list[str] = []
        seen: set[str] = set()
        for method in methods:
            if not isinstance(method, str) or not _METHOD.fullmatch(method.strip()):
                raise InvalidRouteError("Route method is invalid.")
            candidate = method.strip().upper()
            if candidate in seen:
                raise InvalidRouteError(f"Duplicate route method: {candidate}.")
            seen.add(candidate)
            normalized.append(candidate)
        return tuple(normalized)

    def _compile(
        self,
    ) -> tuple[
        str,
        tuple[RouteParameter, ...],
        tuple[int, ...],
        tuple[str, ...],
    ]:
        if self.path == "/":
            return r"^/$", (), (100,), ("static:/",)
        expressions: list[str] = []
        parameters: list[RouteParameter] = []
        precedence: list[int] = []
        signature: list[str] = []
        observed: set[str] = set()
        segments = self.path[1:].split("/")
        for index, segment in enumerate(segments):
            parameter = _PARAMETER.fullmatch(segment)
            if parameter is None:
                if "{" in segment or "}" in segment:
                    raise InvalidRouteError(
                        "Route parameters must occupy a complete path segment."
                    )
                expressions.append(re.escape(segment))
                precedence.append(100)
                signature.append(f"static:{segment}")
                continue
            name = parameter.group("name")
            converter_name = parameter.group("converter") or "str"
            if name in observed:
                raise InvalidRouteError(f"Duplicate route parameter: {name!r}.")
            converter = self._registry.get(converter_name)
            if converter_name == "path" and index != len(segments) - 1:
                raise InvalidRouteError("The path converter must be the final segment.")
            observed.add(name)
            parameters.append(RouteParameter(name, converter_name, converter))
            expressions.append(f"(?P<{name}>{converter.regex})")
            precedence.append(converter.weight)
            signature.append(f"parameter:{converter.regex}:{converter.weight}")
        return (
            "^/" + "/".join(expressions) + "$",
            tuple(parameters),
            tuple(precedence),
            tuple(signature),
        )

    def path_parameters(self, path: str) -> Mapping[str, object] | None:
        if not isinstance(path, str) or not path.startswith("/"):
            return None
        matched = self._pattern.fullmatch(path)
        if matched is None:
            return None
        converted: dict[str, object] = {}
        try:
            for parameter in self.parameters:
                converted[parameter.name] = parameter.converter.parse(
                    matched.group(parameter.name)
                )
        except (TypeError, ValueError, ParameterConversionError):
            return None
        return MappingProxyType(converted)

    def match(self, path: str, method: str) -> RouteMatch | None:
        if not isinstance(method, str) or method.upper() not in self.methods:
            return None
        parameters = self.path_parameters(path)
        if parameters is None:
            return None
        return RouteMatch(self, method.upper(), parameters)

    def build_path(self, parameters: Mapping[str, object]) -> str:
        if not isinstance(parameters, Mapping):
            raise TypeError("Reverse route parameters must be a mapping.")
        expected = {parameter.name for parameter in self.parameters}
        supplied = set(parameters)
        missing = tuple(sorted(expected - supplied))
        extra = tuple(sorted(supplied - expected))
        if missing or extra:
            raise ReverseRouteError(
                f"Reverse route parameters do not match; missing={missing!r}, extra={extra!r}."
            )
        values = {parameter.name: parameter for parameter in self.parameters}

        def replace(matched: re.Match[str]) -> str:
            name = matched.group("name")
            parameter = values[name]
            formatted = parameter.converter.format(parameters[name])
            safe = "/" if parameter.converter_name == "path" else ""
            return quote(formatted, safe=safe)

        return _PARAMETER_INLINE.sub(replace, self.path)
