"""Opaque secret values with safe display and stale-handle protection."""

from __future__ import annotations

import hashlib
import hmac

from .errors import SecretSerializationError, StaleSecretError


MASKED_SECRET = "********"


class SecretValue:
    """Hold sensitive text without exposing it through display or serialization."""

    __slots__ = ("__value", "__fingerprint", "__active")
    __sarathi_secret__ = True

    def __init__(self, value: str) -> None:
        if not isinstance(value, str):
            raise TypeError("Secret values must be strings.")
        self.__value = value
        self.__fingerprint = hashlib.sha256(value.encode("utf-8")).digest()
        self.__active = True

    @property
    def active(self) -> bool:
        return self.__active

    def reveal(self) -> str:
        """Explicitly reveal the current value to trusted application code."""

        if not self.__active:
            raise StaleSecretError("Secret value is stale after rotation or removal.")
        return self.__value

    def matches(self, candidate: str) -> bool:
        if not isinstance(candidate, str):
            return False
        fingerprint = hashlib.sha256(candidate.encode("utf-8")).digest()
        return hmac.compare_digest(self.__fingerprint, fingerprint)

    def _invalidate(self) -> None:
        self.__active = False
        self.__value = ""
        self.__fingerprint = b""

    def __str__(self) -> str:
        return MASKED_SECRET

    def __repr__(self) -> str:
        return f"SecretValue({MASKED_SECRET!r})"

    def __format__(self, format_spec: str) -> str:
        return format(MASKED_SECRET, format_spec)

    def __reduce_ex__(self, protocol: int):
        del protocol
        raise SecretSerializationError("Secret values cannot be serialized or copied.")


def is_secret_value(value: object) -> bool:
    """Recognize SARATHI secret values without importing their concrete type."""

    return getattr(value, "__sarathi_secret__", False) is True
