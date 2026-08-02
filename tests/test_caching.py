"""Tests for the official M29 caching framework."""

from __future__ import annotations

import time
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier

import pytest

from src.caching import (
    CacheAside,
    CacheKeyError,
    CacheLoadError,
    CachePolicy,
    EvictionPolicy,
    InMemoryCache,
    NamespacedCache,
)
from src.metrics import MetricsRegistry


def test_cache_policy_validates_ttl_capacity_and_eviction() -> None:
    with pytest.raises(ValueError, match="TTL"):
        CachePolicy(ttl_seconds=0)
    with pytest.raises(ValueError, match="maximum entries"):
        CachePolicy(max_entries=0)
    with pytest.raises(TypeError, match="EvictionPolicy"):
        CachePolicy(eviction="lru")  # type: ignore[arg-type]


def test_memory_cache_distinguishes_missing_from_cached_none() -> None:
    cache: InMemoryCache[str, object | None] = InMemoryCache()
    assert cache.get("missing").found is False
    cache.set("nullable", None)
    lookup = cache.get("nullable")
    assert lookup.found is True
    assert lookup.value is None


def test_default_ttl_expires_entries_deterministically() -> None:
    now = [10.0]
    cache = InMemoryCache[str, str](
        CachePolicy(ttl_seconds=5),
        clock=lambda: now[0],
    )
    cache.set("key", "value")
    now[0] = 14.999
    assert cache.get("key").found is True
    now[0] = 15.0
    assert cache.get("key").found is False
    assert cache.stats().expirations == 1


def test_per_entry_ttl_overrides_default_policy() -> None:
    now = [0.0]
    cache = InMemoryCache[str, str](
        CachePolicy(ttl_seconds=100),
        clock=lambda: now[0],
    )
    cache.set("short", "value", ttl_seconds=2)
    now[0] = 2.0
    assert cache.get("short").found is False
    with pytest.raises(ValueError, match="TTL"):
        cache.set("invalid", "value", ttl_seconds=-1)


def test_lru_evicts_the_least_recently_used_entry() -> None:
    cache = InMemoryCache[str, int](CachePolicy(max_entries=2))
    cache.set("first", 1)
    cache.set("second", 2)
    cache.get("first")
    cache.set("third", 3)
    assert cache.keys() == ("first", "third")
    assert cache.get("second").found is False
    assert cache.stats().evictions == 1


def test_fifo_ignores_reads_and_updates_without_extra_eviction() -> None:
    cache = InMemoryCache[str, int](
        CachePolicy(max_entries=2, eviction=EvictionPolicy.FIFO)
    )
    cache.set("first", 1)
    cache.set("second", 2)
    cache.get("first")
    cache.set("second", 20)
    cache.set("third", 3)
    assert cache.keys() == ("second", "third")
    assert cache.get("second").value == 20
    assert cache.stats().evictions == 1


def test_expired_entries_are_purged_before_capacity_eviction() -> None:
    now = [0.0]
    cache = InMemoryCache[str, int](
        CachePolicy(max_entries=1),
        clock=lambda: now[0],
    )
    cache.set("expired", 1, ttl_seconds=1)
    now[0] = 2.0
    cache.set("replacement", 2)
    assert cache.keys() == ("replacement",)
    assert cache.stats().expirations == 1
    assert cache.stats().evictions == 0


def test_cache_stats_track_requests_mutations_and_hit_rate() -> None:
    cache = InMemoryCache[str, int]()
    cache.set("first", 1)
    cache.set("second", 2)
    cache.get("first")
    cache.get("missing")
    assert cache.delete("first") is True
    assert cache.delete("first") is False
    assert cache.clear() == 1
    stats = cache.stats()
    assert (stats.entries, stats.hits, stats.misses) == (0, 1, 1)
    assert (stats.writes, stats.deletes) == (2, 2)
    assert stats.hit_rate == 0.5


def test_cache_rejects_unhashable_keys() -> None:
    cache = InMemoryCache()
    with pytest.raises(CacheKeyError, match="hashable"):
        cache.set([], "value")  # type: ignore[arg-type]


def test_namespaces_prevent_collisions_and_clear_independently() -> None:
    backend: InMemoryCache[object, str] = InMemoryCache()
    users = NamespacedCache[str, str](backend, "users")
    sessions = NamespacedCache[str, str](backend, "sessions")
    users.set("same", "user-value")
    sessions.set("same", "session-value")
    assert users.get("same").value == "user-value"
    assert sessions.get("same").value == "session-value"
    assert users.keys() == ("same",)
    assert users.clear() == 1
    assert users.get("same").found is False
    assert sessions.get("same").value == "session-value"


def test_cache_aside_uses_cached_value_without_calling_loader() -> None:
    backend = InMemoryCache[str, int]()
    backend.set("answer", 42)
    aside = CacheAside(backend)
    assert aside.get_or_load(
        "answer",
        lambda: (_ for _ in ()).throw(RuntimeError("must not run")),
    ) == 42


def test_cache_aside_caches_none_as_a_real_value() -> None:
    backend: InMemoryCache[str, object | None] = InMemoryCache()
    aside = CacheAside(backend)
    calls = 0

    def loader() -> None:
        nonlocal calls
        calls += 1
        return None

    assert aside.get_or_load("nullable", loader) is None
    assert aside.get_or_load("nullable", loader) is None
    assert calls == 1


def test_cache_aside_does_not_cache_loader_failures() -> None:
    backend = InMemoryCache[str, str]()
    aside = CacheAside(backend)
    attempts = 0

    def loader() -> str:
        nonlocal attempts
        attempts += 1
        raise RuntimeError("source unavailable")

    for _ in range(2):
        with pytest.raises(CacheLoadError, match="source unavailable"):
            aside.get_or_load("key", loader)
    assert attempts == 2
    assert backend.get("key").found is False


def test_cache_aside_prevents_same_key_stampede() -> None:
    backend = InMemoryCache[str, str]()
    aside = CacheAside(backend)
    calls = 0

    def loader() -> str:
        nonlocal calls
        calls += 1
        time.sleep(0.02)
        return "loaded"

    with ThreadPoolExecutor(max_workers=12) as executor:
        results = tuple(executor.map(lambda _: aside.get_or_load("key", loader), range(30)))
    assert results == ("loaded",) * 30
    assert calls == 1


def test_cache_aside_allows_different_keys_to_load_concurrently() -> None:
    backend = InMemoryCache[str, str]()
    aside = CacheAside(backend)
    barrier = Barrier(2)

    def load(value: str) -> str:
        barrier.wait(timeout=1)
        return value

    with ThreadPoolExecutor(max_workers=2) as executor:
        first = executor.submit(aside.get_or_load, "first", lambda: load("one"))
        second = executor.submit(aside.get_or_load, "second", lambda: load("two"))
        assert {first.result(), second.result()} == {"one", "two"}


def test_cache_aside_detects_reentrant_same_key_loader() -> None:
    backend = InMemoryCache[str, str]()
    aside = CacheAside(backend)
    with pytest.raises(CacheLoadError, match="Re-entrant"):
        aside.get_or_load(
            "key",
            lambda: aside.get_or_load("key", lambda: "nested"),
        )


def test_cache_records_hit_miss_eviction_size_and_latency_metrics() -> None:
    metrics = MetricsRegistry()
    cache = InMemoryCache[str, int](
        CachePolicy(max_entries=1),
        name="profiles",
        metrics=metrics,
    )
    cache.get("missing")
    cache.set("first", 1)
    cache.get("first")
    cache.set("second", 2)
    snapshot = metrics.snapshot()
    labels = (("cache", "profiles"),)
    assert snapshot.find("cache.hits", labels).value == 1  # type: ignore[union-attr]
    assert snapshot.find("cache.misses", labels).value == 1  # type: ignore[union-attr]
    assert snapshot.find("cache.evictions", labels).value == 1  # type: ignore[union-attr]
    assert snapshot.find("cache.entries", labels).value == 1  # type: ignore[union-attr]
    duration = snapshot.find(
        "cache.operation.duration",
        (("cache", "profiles"), ("operation", "get")),
    )
    assert duration is not None and duration.count == 2


def test_memory_cache_remains_bounded_under_concurrent_writes() -> None:
    cache = InMemoryCache[int, int](CachePolicy(max_entries=25))
    with ThreadPoolExecutor(max_workers=8) as executor:
        tuple(executor.map(lambda value: cache.set(value, value), range(200)))
    stats = cache.stats()
    assert stats.entries == 25
    assert stats.writes == 200
    assert stats.evictions == 175
