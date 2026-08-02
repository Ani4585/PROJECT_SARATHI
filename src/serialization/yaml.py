"""Optional safe YAML serializer adapter."""

from __future__ import annotations

from .errors import (
    AdapterUnavailableError,
    SerializationDecodeError,
    SerializationEncodeError,
)


def _yaml_module():
    try:
        import yaml
    except ImportError as error:
        raise AdapterUnavailableError(
            "YAML serialization requires the optional PyYAML dependency."
        ) from error
    return yaml


class YamlSerializer:
    name = "yaml"
    media_type = "application/yaml"

    def dumps(self, value: object) -> str:
        yaml = _yaml_module()
        try:
            return str(
                yaml.safe_dump(
                    value,
                    allow_unicode=True,
                    sort_keys=True,
                )
            )
        except Exception as error:
            raise SerializationEncodeError(
                f"YAML encoding failed: {error}",
                details={"format": self.name, "reason": str(error)},
            ) from error

    def loads(self, document: str) -> object:
        if not isinstance(document, str):
            raise TypeError("Serialized documents must be strings.")
        yaml = _yaml_module()
        try:
            return yaml.safe_load(document)
        except Exception as error:
            raise SerializationDecodeError(
                f"YAML decoding failed: {error}",
                details={"format": self.name, "reason": str(error)},
            ) from error
