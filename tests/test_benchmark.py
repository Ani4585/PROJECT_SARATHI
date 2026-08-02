"""Tests for official M12.5 benchmark regression tooling."""

from __future__ import annotations

import json
from argparse import Namespace
from pathlib import Path

import pytest

from scripts.tooling.benchmark import (
    BenchmarkBaselineError,
    BenchmarkBaselineStore,
    BenchmarkCase,
    BenchmarkJsonRenderer,
    BenchmarkRunner,
    BenchmarkStatus,
    BenchmarkTextRenderer,
)
from scripts.tooling.cli.commands.benchmark import BenchmarkCommand
from scripts.tooling.cli.context import CommandContext


class SequenceClock:
    """Return deterministic clock readings."""

    def __init__(self, *values: float) -> None:
        self._values = iter(values)

    def __call__(self) -> float:
        return next(self._values)


def test_benchmark_case_validates_identity_and_counts() -> None:
    assert BenchmarkCase(" case ", lambda: None, iterations=1, warmups=0).name == "case"
    with pytest.raises(ValueError):
        BenchmarkCase(" ", lambda: None)
    with pytest.raises(ValueError):
        BenchmarkCase("case", lambda: None, iterations=0)
    with pytest.raises(ValueError):
        BenchmarkCase("case", lambda: None, warmups=-1)


def test_runner_measures_and_accepts_result_within_tolerance() -> None:
    runner = BenchmarkRunner(SequenceClock(10.0, 12.0))
    report = runner.run(
        (BenchmarkCase("case", lambda: None, iterations=2, warmups=0),),
        {"case": 0.8},
        tolerance=0.25,
    )
    result = report.results[0]
    assert result.mean_seconds == 1.0
    assert result.status is BenchmarkStatus.PASS
    assert result.change_percent == 25.0
    assert report.passed is True


def test_runner_detects_regression_and_new_baseline() -> None:
    regression = BenchmarkRunner(SequenceClock(0.0, 1.0)).run(
        (BenchmarkCase("slow", lambda: None, iterations=1, warmups=0),),
        {"slow": 0.5},
        tolerance=0.5,
    )
    new = BenchmarkRunner(SequenceClock(0.0, 1.0)).run(
        (BenchmarkCase("new", lambda: None, iterations=1, warmups=0),),
    )
    assert regression.results[0].status is BenchmarkStatus.REGRESSION
    assert regression.passed is False
    assert new.results[0].status is BenchmarkStatus.NEW
    assert new.passed is True


def test_runner_isolates_operation_errors() -> None:
    def broken() -> None:
        raise RuntimeError("boom")

    report = BenchmarkRunner(SequenceClock(0.0)).run(
        (BenchmarkCase("broken", broken, iterations=1, warmups=0),)
    )
    assert report.results[0].status is BenchmarkStatus.ERROR
    assert report.results[0].error == "RuntimeError: boom"
    assert report.errors == 1


def test_runner_rejects_negative_tolerance() -> None:
    with pytest.raises(ValueError):
        BenchmarkRunner().run((), tolerance=-0.1)


def test_baseline_store_round_trip(tmp_path: Path) -> None:
    report = BenchmarkRunner(SequenceClock(0.0, 1.0)).run(
        (BenchmarkCase("case", lambda: None, iterations=2, warmups=0),)
    )
    store = BenchmarkBaselineStore(tmp_path / "baseline.json")
    store.save(report)
    assert store.load() == {"case": 0.5}
    document = json.loads(store.path.read_text(encoding="utf-8"))
    assert document["schema_version"] == 1


def test_baseline_store_rejects_invalid_document(tmp_path: Path) -> None:
    path = tmp_path / "baseline.json"
    path.write_text('{"schema_version": 2, "benchmarks": {}}', encoding="utf-8")
    with pytest.raises(BenchmarkBaselineError):
        BenchmarkBaselineStore(path).load()


def test_renderers_expose_human_and_machine_results() -> None:
    report = BenchmarkRunner(SequenceClock(0.0, 1.0)).run(
        (BenchmarkCase("case", lambda: None, iterations=1, warmups=0),)
    )
    assert "[NEW] case" in BenchmarkTextRenderer().render(report)
    document = json.loads(BenchmarkJsonRenderer().render(report))
    assert document["summary"]["passed"] is True
    assert document["results"][0]["name"] == "case"


def test_benchmark_command_updates_baseline(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    command = BenchmarkCommand(
        BenchmarkRunner(SequenceClock(0.0, 1.0)),
        lambda root: (BenchmarkCase("case", lambda: root, iterations=1, warmups=0),),
    )
    exit_code = command.execute(
        CommandContext(tmp_path, "python"),
        Namespace(
            baseline=Path("baseline.json"),
            tolerance=0.25,
            format="text",
            update_baseline=True,
        ),
    )
    assert exit_code == 0
    assert BenchmarkBaselineStore(tmp_path / "baseline.json").load() == {"case": 1.0}
    assert "Baseline updated" in capsys.readouterr().out


def test_benchmark_command_returns_regression_exit_code(tmp_path: Path) -> None:
    baseline = tmp_path / "baseline.json"
    baseline.write_text(
        '{"schema_version": 1, "benchmarks": {"case": 0.5}}',
        encoding="utf-8",
    )
    command = BenchmarkCommand(
        BenchmarkRunner(SequenceClock(0.0, 1.0)),
        lambda root: (BenchmarkCase("case", lambda: root, iterations=1, warmups=0),),
    )
    exit_code = command.execute(
        CommandContext(tmp_path, "python"),
        Namespace(
            baseline=baseline,
            tolerance=0.25,
            format="json",
            update_baseline=False,
        ),
    )
    assert exit_code == 1
