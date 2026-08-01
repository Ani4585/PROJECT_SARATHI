"""Configuration key normalization helpers."""

from __future__ import annotations


def normalize_key(key: str) -> str:
    """Return a canonical, case-insensitive dotted configuration key."""

    normalized = key.strip().lower().replace("__", ".")
    if not normalized or any(not part for part in normalized.split(".")):
        raise ValueError("Configuration keys must contain non-blank segments.")
    return normalized
