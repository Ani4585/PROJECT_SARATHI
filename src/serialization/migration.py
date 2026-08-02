"""Schema-version envelopes and deterministic forward migration hooks."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass

from .contracts import Serializer
from .errors import MigrationError, SerializationDecodeError


MigrationHook = Callable[[object], object]


@dataclass(frozen=True, slots=True)
class MigrationStep:
    schema: str
    from_version: int
    to_version: int
    migrate: MigrationHook


class MigrationRegistry:
    def __init__(self) -> None:
        self._steps: dict[str, dict[int, MigrationStep]] = {}

    def register(
        self,
        schema: str,
        from_version: int,
        to_version: int,
        migrate: MigrationHook,
    ) -> None:
        schema = schema.strip()
        if not schema:
            raise ValueError("Migration schema must not be blank.")
        if (
            not isinstance(from_version, int)
            or isinstance(from_version, bool)
            or not isinstance(to_version, int)
            or isinstance(to_version, bool)
        ):
            raise TypeError("Migration versions must be integers.")
        if from_version < 1 or to_version <= from_version:
            raise ValueError("Migration versions must move forward from version 1 or later.")
        if not callable(migrate):
            raise TypeError("Migration hook must be callable.")
        steps = self._steps.setdefault(schema, {})
        if from_version in steps:
            raise ValueError(f"Migration already registered: {schema} v{from_version}")
        steps[from_version] = MigrationStep(schema, from_version, to_version, migrate)

    def migrate(
        self,
        schema: str,
        value: object,
        from_version: int,
        to_version: int,
    ) -> object:
        if from_version > to_version:
            raise MigrationError("Backward schema migration is not supported.")
        current = from_version
        migrated = value
        observed: set[int] = set()
        while current < to_version:
            if current in observed:
                raise MigrationError(f"Migration cycle detected for {schema} at v{current}.")
            observed.add(current)
            try:
                step = self._steps[schema][current]
            except KeyError as error:
                raise MigrationError(
                    f"No migration path for {schema} from v{current} to v{to_version}."
                ) from error
            if step.to_version > to_version:
                raise MigrationError(
                    f"Migration for {schema} overshoots target v{to_version}."
                )
            try:
                migrated = step.migrate(migrated)
            except Exception as error:
                raise MigrationError(
                    f"Migration for {schema} v{current}->v{step.to_version} failed: {error}"
                ) from error
            current = step.to_version
        return migrated


class VersionedSerializer:
    """Wrap serialized payloads with schema identity and migrate older versions."""

    def __init__(
        self,
        serializer: Serializer,
        *,
        schema: str,
        version: int,
        migrations: MigrationRegistry | None = None,
    ) -> None:
        schema = schema.strip()
        if not schema:
            raise ValueError("Serialization schema must not be blank.")
        if not isinstance(version, int) or isinstance(version, bool) or version < 1:
            raise ValueError("Serialization schema version must be a positive integer.")
        self._serializer = serializer
        self.schema = schema
        self.version = version
        self.migrations = migrations or MigrationRegistry()

    @property
    def name(self) -> str:
        return self._serializer.name

    @property
    def media_type(self) -> str:
        return self._serializer.media_type

    def dumps(self, value: object) -> str:
        return self._serializer.dumps(
            {"$schema": self.schema, "$version": self.version, "payload": value}
        )

    def loads(self, document: str) -> object:
        envelope = self._serializer.loads(document)
        if not isinstance(envelope, Mapping):
            raise SerializationDecodeError("Versioned document must be a mapping.")
        if set(envelope) != {"$schema", "$version", "payload"}:
            raise SerializationDecodeError("Versioned document envelope is invalid.")
        schema = envelope["$schema"]
        version = envelope["$version"]
        if schema != self.schema:
            raise SerializationDecodeError(
                f"Unexpected schema {schema!r}; expected {self.schema!r}."
            )
        if not isinstance(version, int) or isinstance(version, bool) or version < 1:
            raise SerializationDecodeError("Document schema version must be a positive integer.")
        if version > self.version:
            raise MigrationError(
                f"Document schema v{version} is newer than supported v{self.version}."
            )
        return self.migrations.migrate(
            self.schema,
            envelope["payload"],
            version,
            self.version,
        )
