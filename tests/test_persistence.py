"""Tests for the M17 persistence ports and in-memory adapter."""

from __future__ import annotations

from dataclasses import dataclass

import pytest

from src.persistence import (
    EntityAlreadyExistsError,
    EntityNotFoundError,
    InMemoryRepository,
    InMemoryUnitOfWork,
    UnitOfWorkState,
)


@dataclass
class Item:
    identifier: str
    value: int


def make_repository() -> InMemoryRepository[Item, str]:
    return InMemoryRepository(lambda item: item.identifier)


def test_repository_adds_gets_and_lists_in_order() -> None:
    repository = make_repository()
    first = Item("one", 1)
    second = Item("two", 2)
    repository.add(first)
    repository.add(second)
    assert repository.get("one") is first
    assert repository.list() == (first, second)
    assert len(repository) == 2


def test_repository_rejects_duplicate_identity() -> None:
    repository = make_repository()
    repository.add(Item("one", 1))
    with pytest.raises(EntityAlreadyExistsError):
        repository.add(Item("one", 2))


def test_repository_require_reports_missing_entity() -> None:
    with pytest.raises(EntityNotFoundError):
        make_repository().require("missing")


def test_repository_remove_returns_entity() -> None:
    repository = make_repository()
    item = Item("one", 1)
    repository.add(item)
    assert repository.remove("one") is item
    assert repository.get("one") is None


def test_repository_remove_reports_missing_entity() -> None:
    with pytest.raises(EntityNotFoundError):
        make_repository().remove("missing")


def test_repository_snapshot_and_restore_are_deep() -> None:
    repository = make_repository()
    item = Item("one", 1)
    repository.add(item)
    snapshot = repository.snapshot()
    item.value = 9
    repository.restore(snapshot)
    assert repository.require("one").value == 1


def test_unit_of_work_commits_successful_context() -> None:
    repository = make_repository()
    unit = InMemoryUnitOfWork()
    unit.register_repository("items", repository)
    with unit:
        unit.repository("items").add(Item("one", 1))
    assert unit.state is UnitOfWorkState.COMMITTED
    assert repository.require("one").value == 1


def test_unit_of_work_rolls_back_exception() -> None:
    repository = make_repository()
    repository.add(Item("one", 1))
    unit = InMemoryUnitOfWork()
    unit.register_repository("items", repository)
    with pytest.raises(RuntimeError, match="boom"):
        with unit:
            repository.require("one").value = 9
            repository.add(Item("two", 2))
            raise RuntimeError("boom")
    assert unit.state is UnitOfWorkState.ROLLED_BACK
    assert repository.require("one").value == 1
    assert repository.get("two") is None


def test_unit_of_work_supports_explicit_rollback() -> None:
    repository = make_repository()
    unit = InMemoryUnitOfWork()
    unit.register_repository("items", repository)
    with unit:
        repository.add(Item("one", 1))
        unit.rollback()
    assert repository.get("one") is None


def test_unit_of_work_rejects_duplicate_repository() -> None:
    unit = InMemoryUnitOfWork()
    unit.register_repository("items", make_repository())
    with pytest.raises(ValueError):
        unit.register_repository("items", make_repository())


def test_unit_of_work_rejects_registration_while_active() -> None:
    unit = InMemoryUnitOfWork()
    with unit:
        with pytest.raises(RuntimeError):
            unit.register_repository("items", make_repository())


def test_unit_of_work_rejects_commit_when_inactive() -> None:
    with pytest.raises(RuntimeError):
        InMemoryUnitOfWork().commit()
