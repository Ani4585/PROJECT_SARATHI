"""
PROJECT SARATHI

Centralised project path definitions.
"""

from pathlib import Path

# Root directory of the project
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Core directories
CONFIG_DIR = PROJECT_ROOT / "config"
DATA_DIR = PROJECT_ROOT / "data"
LOG_DIR = PROJECT_ROOT / "logs"
SRC_DIR = PROJECT_ROOT / "src"
TESTS_DIR = PROJECT_ROOT / "tests"
DOCS_DIR = PROJECT_ROOT / "docs"

# Create required directories if they do not already exist
for directory in (
    DATA_DIR,
    LOG_DIR,
):
    directory.mkdir(parents=True, exist_ok=True)