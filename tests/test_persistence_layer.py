"""Tests for the official M30 persistence layer."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from threading import Barrier

import pytest

from examples.persistence.transactional_repository import main as example_main
from src.configuration import Configuration
from src.container import ServiceContainer
from src.health import HealthStatus
from src.persistence import (
    ActiveSessionError,
    DatabaseState,
    EntityAlreadyExistsError,
    EntityNotFoundError,
    InMemoryDatabase,
    PersistenceConfigurationError,
    PersistenceConnection,
    PersistenceConnectionError,
    PersistenceHealthCheck,
    PersistenceRuntime,
    PersistenceSession,
    PersistenceSessionError,
    PersistenceSettings,
    SessionFactory,
    SessionState,
    TransactionConflictError,
    UnitOfWorkState,
    create_persistence_runtime,
    persistence_resource,
    register_persistence,
)
from src.resources import ResourceRegistry


@dataclass(slots=True)
class Record:
    identifier: str
    value: int


def identity(record: Record) -> str:
    return record.identifier


def test_settings_load_from_layered_configuration_and_mapping() -> None:
    configuration = Configuration(
        {
            "persistence.adapter": "MEMORY",
            "persistence.database_name": "primary",
        }
    )
    assert PersistenceSettings.from_configuration(configuration) == PersistenceSettings(
        "memory", "primary"
    )
    assert PersistenceSettings.from_configuration(
        {"persistence.database_name": "mapped"}
    ).database_name == "mapped"


def test_settings_reject_unsupported_or_invalid_values() -> None:
    with pytest.raises(PersistenceConfigurationError, match="Unsupported"):
        PersistenceSettings("postgres", "database")
    with pytest.raises(PersistenceConfigurationError, match="must be strings"):
        PersistenceSettings.from_configuration({"persistence.adapter": 1})
    with pytest.raises(PersistenceConfigurationError, match="must not be blank"):
        PersistenceSettings("memory", " ")


def test_database_connection_lifecycle_and_contracts() -> None:
    database = InMemoryDatabase("test")
    assert database.state is DatabaseState.CLOSED
    database.open()
    connection = database.connect()
    assert isinstance(connection, PersistenceConnection)
    assert isinstance(connection, SessionFactory)
    assert connection.healthy is True
    connection.close()
    database.close()
    assert database.state is DatabaseState.CLOSED


def test_session_commit_persists_repository_changes() -> None:
    with create_persistence_runtime() as runtime:
        session = runtime.session_factory.open_session()
        assert isinstance(session, PersistenceSession)
        with session:
            records = session.repository("records", identity)
            records.add(Record("one", 1))
        with runtime.session_factory.open_session() as verify:
            assert verify.repository("records", identity).require("one").value == 1


def test_session_exception_rolls_back_changes() -> None:
    with create_persistence_runtime() as runtime:
        with pytest.raises(RuntimeError, match="rollback"):
            with runtime.session_factory.open_session() as session:
                session.repository("records", identity).add(Record("one", 1))
                raise RuntimeError("rollback")
        with runtime.session_factory.open_session() as verify:
            assert verify.repository("records", identity).get("one") is None


def test_explicit_session_rollback_discards_changes() -> None:
    with create_persistence_runtime() as runtime:
        session = runtime.session_factory.open_session()
        session.begin()
        records = session.repository("records", identity)
        records.add(Record("one", 1))
        session.rollback()
        assert session.state is SessionState.ROLLED_BACK
        session.close()
        with runtime.session_factory.open_session() as verify:
            assert verify.repository("records", identity).get("one") is None


def test_session_repository_enforces_identity_and_active_boundary() -> None:
    with create_persistence_runtime() as runtime:
        session = runtime.session_factory.open_session()
        session.begin()
        records = session.repository("records", identity)
        records.add(Record("one", 1))
        with pytest.raises(EntityAlreadyExistsError):
            records.add(Record("one", 2))
        with pytest.raises(EntityNotFoundError):
            records.require("missing")
        session.commit()
        with pytest.raises(PersistenceSessionError, match="not active"):
            records.list()
        session.close()


def test_one_transaction_commits_multiple_repositories_atomically() -> None:
    with create_persistence_runtime() as runtime:
        with runtime.unit_of_work() as work:
            work.repository("first", identity).add(Record("one", 1))
            work.repository("second", identity).add(Record("two", 2))
        with runtime.unit_of_work() as verify:
            assert verify.repository("first", identity).require("one").value == 1
            assert verify.repository("second", identity).require("two").value == 2


def test_uncommitted_data_is_isolated_from_other_sessions() -> None:
    with create_persistence_runtime() as runtime:
        first = runtime.session_factory.open_session()
        second = runtime.session_factory.open_session()
        first.begin()
        second.begin()
        first.repository("records", identity).add(Record("one", 1))
        assert second.repository("records", identity).get("one") is None
        first.commit()
        second.rollback()
        first.close()
        second.close()
        with runtime.unit_of_work() as verify:
            assert verify.repository("records", identity).require("one").value == 1


def test_optimistic_conflict_rejects_stale_commit() -> None:
    with create_persistence_runtime() as runtime:
        first = runtime.session_factory.open_session()
        second = runtime.session_factory.open_session()
        first.begin()
        second.begin()
        first.repository("records", identity).add(Record("one", 1))
        second.repository("records", identity).add(Record("two", 2))
        first.commit()
        with pytest.raises(TransactionConflictError, match="newer committed"):
            second.commit()
        assert second.state is SessionState.FAILED
        first.close()
        second.close()


def test_session_unit_of_work_commits_and_reports_state() -> None:
    with create_persistence_runtime() as runtime:
        work = runtime.unit_of_work()
        with work:
            work.repository("records", identity).add(Record("one", 1))
        assert work.state is UnitOfWorkState.COMMITTED
        with runtime.unit_of_work() as verify:
            assert verify.repository("records", identity).require("one").value == 1


def test_session_unit_of_work_supports_explicit_rollback() -> None:
    with create_persistence_runtime() as runtime:
        work = runtime.unit_of_work()
        with work:
            work.repository("records", identity).add(Record("one", 1))
            work.rollback()
        assert work.state is UnitOfWorkState.ROLLED_BACK
        with runtime.unit_of_work() as verify:
            assert verify.repository("records", identity).get("one") is None


def test_session_unit_of_work_rolls_back_body_failure() -> None:
    with create_persistence_runtime() as runtime:
        work = runtime.unit_of_work()
        with pytest.raises(ValueError, match="body"):
            with work:
                work.repository("records", identity).add(Record("one", 1))
                raise ValueError("body")
        assert work.state is UnitOfWorkState.ROLLED_BACK


def test_connection_refuses_close_with_active_session() -> None:
    runtime = create_persistence_runtime().open()
    session = runtime.session_factory.open_session()
    session.begin()
    with pytest.raises(ActiveSessionError, match="active session"):
        runtime.close()
    assert runtime.healthy is True
    session.rollback()
    session.close()
    runtime.close()
    assert runtime.healthy is False


def test_persistence_health_tracks_runtime_connection() -> None:
    runtime = create_persistence_runtime(
        {"persistence.database_name": "health"}
    )
    check = PersistenceHealthCheck(runtime)
    assert check.run().status is HealthStatus.UNHEALTHY
    runtime.open()
    result = check.run()
    assert result.status is HealthStatus.HEALTHY
    assert result.details == ("Adapter: memory", "Database: health")
    runtime.close()


def test_dependency_injection_registers_runtime_database_and_transient_units() -> None:
    container = ServiceContainer()
    runtime = register_persistence(
        container,
        Configuration({"persistence.database_name": "injected"}),
    )
    assert container.resolve_type(PersistenceRuntime) is runtime
    assert container.resolve_type(InMemoryDatabase) is runtime.database
    assert container.resolve("persistence.runtime") is runtime
    runtime.open()
    first = container.resolve("persistence.unit_of_work")
    second = container.resolve("persistence.unit_of_work")
    assert first is not second
    runtime.close()


def test_resource_registry_owns_persistence_runtime_lifecycle() -> None:
    registry = ResourceRegistry()
    registry.register(
        persistence_resource({"persistence.database_name": "managed"})
    )
    with registry:
        runtime = registry.get("persistence")
        assert isinstance(runtime, PersistenceRuntime)
        assert runtime.healthy is True
        with runtime.unit_of_work() as work:
            work.repository("records", identity).add(Record("one", 1))
    assert runtime.healthy is False


def test_reference_example_demonstrates_commit_and_rollback(capsys) -> None:
    example_main()
    assert capsys.readouterr().out.splitlines() == [
        "Committed: sarathi | PROJECT SARATHI",
        "Rows after rollback: 1",
    ]


def test_concurrent_commits_allow_exactly_one_snapshot_winner() -> None:
    with create_persistence_runtime() as runtime:
        sessions = [runtime.session_factory.open_session() for _ in range(2)]
        for index, session in enumerate(sessions):
            session.begin()
            session.repository("records", identity).add(Record(str(index), index))
        barrier = Barrier(2)

        def commit(session) -> str:
            barrier.wait(timeout=1)
            try:
                session.commit()
            except TransactionConflictError:
                return "conflict"
            return "committed"

        with ThreadPoolExecutor(max_workers=2) as executor:
            outcomes = tuple(executor.map(commit, sessions))
        assert sorted(outcomes) == ["committed", "conflict"]
        for session in sessions:
            session.close()
        with runtime.unit_of_work() as verify:
            assert len(verify.repository("records", identity)) == 1


def test_runtime_requires_open_connection_for_units_of_work() -> None:
    runtime = create_persistence_runtime()
    with pytest.raises(PersistenceConnectionError, match="not open"):
        runtime.unit_of_work()
