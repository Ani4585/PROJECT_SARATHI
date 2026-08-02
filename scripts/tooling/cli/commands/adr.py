"""Architecture Decision Record lifecycle CLI."""

from __future__ import annotations

from argparse import ArgumentParser, Namespace

from src.adr import AdrRepository, AdrRepositoryError, AdrStatus

from ...console import print_error, print_header
from ..command import Command
from ..context import CommandContext


class AdrCommand(Command):
    @property
    def name(self) -> str:
        return "adr"

    @property
    def description(self) -> str:
        return "Create and manage architecture decision records."

    @staticmethod
    def _content(parser: ArgumentParser) -> None:
        parser.add_argument("--title", required=True)
        parser.add_argument("--context", required=True)
        parser.add_argument("--decision", required=True)
        parser.add_argument("--consequences", required=True)

    def configure_parser(self, parser: ArgumentParser) -> None:
        actions = parser.add_subparsers(dest="adr_action", required=True)
        create = actions.add_parser("create")
        self._content(create)
        create.add_argument("--status", choices=tuple(status.value for status in AdrStatus), default=AdrStatus.PROPOSED.value)
        create.add_argument("--link", action="append", default=[])
        actions.add_parser("list")
        show = actions.add_parser("show")
        show.add_argument("number", type=int)
        supersede = actions.add_parser("supersede")
        supersede.add_argument("number", type=int)
        self._content(supersede)
        actions.add_parser("validate")
        actions.add_parser("index")

    def execute(self, context: CommandContext, arguments: Namespace) -> int:
        print_header("CLI - ADR")
        repository = AdrRepository(context.project_root / "docs" / "adr")
        action = arguments.adr_action
        try:
            if action == "create":
                record = repository.create(
                    arguments.title,
                    arguments.context,
                    arguments.decision,
                    arguments.consequences,
                    status=AdrStatus(arguments.status),
                    links=tuple(arguments.link),
                )
                print(f"Created {record.identifier}: {record.title}")
            elif action == "list":
                for record in repository.list():
                    print(f"{record.identifier} | {record.status.value} | {record.title}")
            elif action == "show":
                record = repository.get(arguments.number)
                print(f"{record.identifier}: {record.title}")
                print(f"Status: {record.status.value}")
                print(f"Date: {record.decided_on.isoformat()}")
                print(f"\nContext\n{record.context}\n\nDecision\n{record.decision}\n\nConsequences\n{record.consequences}")
            elif action == "supersede":
                record = repository.supersede(
                    arguments.number,
                    arguments.title,
                    arguments.context,
                    arguments.decision,
                    arguments.consequences,
                )
                print(f"Created {record.identifier}; superseded ADR-{arguments.number:04d}.")
            elif action == "validate":
                errors = repository.validate()
                if errors:
                    for error in errors:
                        print_error(error)
                    return 1
                print(f"ADR validation passed: {len(repository.list())} records.")
            elif action == "index":
                print(f"ADR index: {repository.generate_index()}")
            return 0
        except (AdrRepositoryError, OSError, ValueError) as error:
            print_error(str(error))
            return 1
