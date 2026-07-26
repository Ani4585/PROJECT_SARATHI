from pathlib import Path

PROJECT_ROOT = Path.cwd()

DIRECTORIES = [
    "app",
    "app/core",
    "app/cli",
    "app/config",
    "app/builders",
    "app/engines",
    "app/generators",
    "app/models",
    "app/utils",
    "app/services",
    "app/database",
    "app/assets",
    "knowledge",
    "knowledge/policy",
    "knowledge/finance",
    "knowledge/engineering",
    "knowledge/feedstocks",
    "knowledge/esg",
    "knowledge/case_studies",
    "knowledge/governance",
    "knowledge/technology",
    "datasets",
    "templates",
    "exports",
    "output",
    "figures",
    "maps",
    "reports",
    "logs",
    "tests",
    "docs",
]

for directory in DIRECTORIES:
    (PROJECT_ROOT / directory).mkdir(parents=True, exist_ok=True)

print("PROJECT STRUCTURE CREATED SUCCESSFULLY")
