"""Filesystem ADR repository, validation, rendering, and index generation."""

from __future__ import annotations

import re
from datetime import date
from pathlib import Path

from .model import AdrStatus, ArchitectureDecision


_HEADER = re.compile(r"^# (ADR-(\d{4})): (.+)$")


class AdrRepositoryError(ValueError):
    pass


class AdrRepository:
    def __init__(self, directory: Path) -> None:
        self.directory = directory.resolve()

    def list(self) -> tuple[ArchitectureDecision, ...]:
        if not self.directory.is_dir():
            return ()
        records = tuple(self._parse(path) for path in sorted(self.directory.glob("[0-9][0-9][0-9][0-9]-*.md")))
        numbers = [record.number for record in records]
        if len(numbers) != len(set(numbers)):
            raise AdrRepositoryError("Duplicate ADR numbers were found.")
        return tuple(sorted(records, key=lambda record: record.number))

    def get(self, number: int) -> ArchitectureDecision:
        try:
            return next(record for record in self.list() if record.number == number)
        except StopIteration as error:
            raise AdrRepositoryError(f"ADR-{number:04d} was not found.") from error

    def create(
        self,
        title: str,
        context: str,
        decision: str,
        consequences: str,
        *,
        status: AdrStatus = AdrStatus.PROPOSED,
        decided_on: date | None = None,
        links: tuple[str, ...] = (),
        supersedes: int | None = None,
    ) -> ArchitectureDecision:
        records = self.list()
        number = records[-1].number + 1 if records else 1
        record = ArchitectureDecision(
            number,
            title,
            status,
            decided_on or date.today(),
            context,
            decision,
            consequences,
            links,
            supersedes,
        )
        if supersedes is not None:
            self.get(supersedes)
        self._write(record)
        self.generate_index()
        return record

    def supersede(
        self,
        number: int,
        title: str,
        context: str,
        decision: str,
        consequences: str,
    ) -> ArchitectureDecision:
        previous = self.get(number)
        if previous.status is AdrStatus.SUPERSEDED:
            raise AdrRepositoryError(f"{previous.identifier} is already superseded.")
        replacement = self.create(
            title,
            context,
            decision,
            consequences,
            status=AdrStatus.ACCEPTED,
            supersedes=number,
        )
        self._write(previous.with_status(AdrStatus.SUPERSEDED, superseded_by=replacement.number))
        self.generate_index()
        return replacement

    def validate(self) -> tuple[str, ...]:
        errors: list[str] = []
        records = self.list()
        numbers = {record.number for record in records}
        for record in records:
            if record.supersedes is not None and record.supersedes not in numbers:
                errors.append(f"{record.identifier}: missing superseded ADR-{record.supersedes:04d}")
            if record.superseded_by is not None and record.superseded_by not in numbers:
                errors.append(f"{record.identifier}: missing replacement ADR-{record.superseded_by:04d}")
            for link in record.links:
                if link.startswith(("https://", "http://", "#")):
                    continue
                if not (self.directory / link).resolve().is_file():
                    errors.append(f"{record.identifier}: broken link {link}")
        return tuple(errors)

    def generate_index(self) -> Path:
        self.directory.mkdir(parents=True, exist_ok=True)
        lines = ["# Architecture Decision Record Index", "", "| ADR | Title | Status | Date |", "|-----|-------|--------|------|"]
        for record in self.list():
            lines.append(
                f"| [{record.identifier}]({record.filename}) | {record.title} | {record.status.value} | {record.decided_on.isoformat()} |"
            )
        path = self.directory / "README.md"
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        return path

    def _write(self, record: ArchitectureDecision) -> Path:
        self.directory.mkdir(parents=True, exist_ok=True)
        existing = tuple(self.directory.glob(f"{record.number:04d}-*.md"))
        path = existing[0] if existing else self.directory / record.filename
        links = "\n".join(f"- {link}" for link in record.links) or "- None"
        metadata = [
            f"- Status: {record.status.value}",
            f"- Date: {record.decided_on.isoformat()}",
            f"- Supersedes: {f'ADR-{record.supersedes:04d}' if record.supersedes else 'None'}",
            f"- Superseded by: {f'ADR-{record.superseded_by:04d}' if record.superseded_by else 'None'}",
        ]
        content = (
            f"# {record.identifier}: {record.title}\n\n"
            + "\n".join(metadata)
            + f"\n\n## Context\n\n{record.context}\n\n## Decision\n\n{record.decision}\n\n"
            + f"## Consequences\n\n{record.consequences}\n\n## Links\n\n{links}\n"
        )
        path.write_text(content, encoding="utf-8")
        return path

    def _parse(self, path: Path) -> ArchitectureDecision:
        text = path.read_text(encoding="utf-8-sig")
        lines = text.splitlines()
        match = _HEADER.match(lines[0]) if lines else None
        if not match:
            raise AdrRepositoryError(f"Invalid ADR heading: {path.name}")
        number = int(match.group(2))
        title = match.group(3).strip()
        metadata: dict[str, str] = {}
        for line in lines[1:8]:
            if line.startswith("- ") and ": " in line:
                key, value = line[2:].split(": ", 1)
                metadata[key] = value

        def section(name: str, next_name: str | None) -> str:
            try:
                start = lines.index(f"## {name}") + 1
                end = lines.index(f"## {next_name}") if next_name else len(lines)
            except ValueError as error:
                raise AdrRepositoryError(f"Invalid ADR metadata in {path.name}: missing {name} section") from error
            return "\n".join(lines[start:end]).strip()

        links_text = section("Links", None)
        links = tuple(line[2:].strip() for line in links_text.splitlines() if line.startswith("- ") and line[2:].strip() != "None")

        def adr_number(value: str | None) -> int | None:
            return None if not value or value == "None" else int(value.removeprefix("ADR-"))

        try:
            return ArchitectureDecision(
                number,
                title,
                AdrStatus(metadata["Status"]),
                date.fromisoformat(metadata["Date"]),
                section("Context", "Decision"),
                section("Decision", "Consequences"),
                section("Consequences", "Links"),
                links,
                adr_number(metadata.get("Supersedes")),
                adr_number(metadata.get("Superseded by")),
            )
        except (KeyError, ValueError) as error:
            raise AdrRepositoryError(f"Invalid ADR metadata in {path.name}: {error}") from error
