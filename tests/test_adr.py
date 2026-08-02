"""Tests for official M17 Architecture Decision Records."""

from __future__ import annotations

from argparse import Namespace
from datetime import date
from pathlib import Path

import pytest

from scripts.tooling.cli.commands.adr import AdrCommand
from scripts.tooling.cli.context import CommandContext
from src.adr import AdrRepository, AdrRepositoryError, AdrStatus, ArchitectureDecision


def create_record(repository: AdrRepository, title: str = "Use a Boundary"):
    return repository.create(
        title,
        "A stable boundary is required.",
        "Use an explicit contract.",
        "The boundary is testable.",
        status=AdrStatus.ACCEPTED,
        decided_on=date(2026, 8, 2),
    )


def test_model_validates_and_formats_identity() -> None:
    record = ArchitectureDecision(1, " Decision ", AdrStatus.PROPOSED, date(2026, 8, 2), " Context ", " Decide ", " Consequence ")
    assert record.identifier == "ADR-0001"
    assert record.filename == "0001-decision.md"
    with pytest.raises(ValueError):
        ArchitectureDecision(0, "Title", AdrStatus.PROPOSED, date.today(), "c", "d", "x")


def test_repository_creates_reads_and_indexes_records(tmp_path: Path) -> None:
    repository = AdrRepository(tmp_path / "adr")
    first = create_record(repository)
    second = create_record(repository, "Keep Determinism")
    assert (first.number, second.number) == (1, 2)
    assert repository.get(1) == first
    index = repository.generate_index().read_text(encoding="utf-8")
    assert "ADR-0001" in index and "ADR-0002" in index


def test_supersede_creates_replacement_and_updates_previous(tmp_path: Path) -> None:
    repository = AdrRepository(tmp_path / "adr")
    previous = create_record(repository)
    replacement = repository.supersede(
        previous.number,
        "Replace Boundary",
        "Requirements changed.",
        "Use the replacement.",
        "Existing users migrate.",
    )
    assert replacement.supersedes == previous.number
    assert replacement.status is AdrStatus.ACCEPTED
    assert repository.get(previous.number).status is AdrStatus.SUPERSEDED
    assert repository.get(previous.number).superseded_by == replacement.number


def test_repository_rejects_repeated_supersede(tmp_path: Path) -> None:
    repository = AdrRepository(tmp_path / "adr")
    previous = create_record(repository)
    repository.supersede(previous.number, "Replacement", "Context", "Decision", "Consequences")
    with pytest.raises(AdrRepositoryError, match="already superseded"):
        repository.supersede(previous.number, "Again", "Context", "Decision", "Consequences")


def test_validation_reports_broken_relative_link(tmp_path: Path) -> None:
    repository = AdrRepository(tmp_path / "adr")
    repository.create("Linked", "Context", "Decision", "Consequences", links=("missing.md",))
    assert repository.validate() == ("ADR-0001: broken link missing.md",)


def test_invalid_metadata_is_rejected(tmp_path: Path) -> None:
    directory = tmp_path / "adr"
    directory.mkdir()
    (directory / "0001-broken.md").write_text("# ADR-0001: Broken\n", encoding="utf-8")
    with pytest.raises(AdrRepositoryError, match="Invalid ADR metadata"):
        AdrRepository(directory).list()


def test_cli_create_list_show_validate_and_index(tmp_path: Path, capsys) -> None:
    command = AdrCommand()
    context = CommandContext(tmp_path, "python")
    create = Namespace(
        adr_action="create",
        title="Decision",
        context="Context",
        decision="Decision",
        consequences="Consequences",
        status="Accepted",
        link=[],
    )
    assert command.execute(context, create) == 0
    assert command.execute(context, Namespace(adr_action="list")) == 0
    assert command.execute(context, Namespace(adr_action="show", number=1)) == 0
    assert command.execute(context, Namespace(adr_action="validate")) == 0
    assert command.execute(context, Namespace(adr_action="index")) == 0
    output = capsys.readouterr().out
    assert "ADR-0001" in output
    assert "ADR validation passed" in output


def test_repository_retrospective_records_are_valid() -> None:
    repository = AdrRepository(Path(__file__).resolve().parents[1] / "docs" / "adr")
    assert len(repository.list()) == 4
    assert repository.validate() == ()
    assert all(record.status is AdrStatus.ACCEPTED for record in repository.list())
