"""Generate PROJECT SARATHI source coverage reports."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Direct script execution places ``scripts`` rather than the repository root on
# sys.path. Add the root before importing the package-qualified tooling modules.
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.tooling.coverage import (
    DEFAULT_COVERAGE_THRESHOLD,
    CoverageReportWriter,
    collect_pytest_coverage,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Collect PROJECT SARATHI source coverage.")
    parser.add_argument("--threshold", type=float, default=DEFAULT_COVERAGE_THRESHOLD)
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("reports/coverage"),
        help="Directory for JSON and HTML coverage reports.",
    )
    arguments = parser.parse_args()
    report = collect_pytest_coverage(PROJECT_ROOT, threshold=arguments.threshold)
    writer = CoverageReportWriter()
    output = (PROJECT_ROOT / arguments.output).resolve()
    writer.write_json(report, output / "coverage.json")
    writer.write_html(report, output / "coverage.html")
    print(writer.render_text(report))
    print(f"JSON report: {output / 'coverage.json'}")
    print(f"HTML report: {output / 'coverage.html'}")
    return 0 if report.passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
