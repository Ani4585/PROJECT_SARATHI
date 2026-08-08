import sys
from pathlib import Path

def write_file(path_str: str, content: str):
    p = Path(path_str)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content.strip() + "\n", encoding="utf-8")
    print(f"[UPDATED] {path_str}")

SARATHI_INIT = '''
import sys
from pathlib import Path

_pkg_dir = Path(__file__).resolve().parent
_root_dir = str(_pkg_dir.parent.parent if _pkg_dir.parent.name == "src" else _pkg_dir.parent)
if _root_dir not in sys.path:
    sys.path.insert(0, _root_dir)

from scripts.tooling.cli.application import create_cli_application

def main(arguments=None) -> int:
    module = sys.modules[__name__]
    app_factory = getattr(module, "create_cli_application", create_cli_application)
    app = app_factory()
    return app.run(arguments)

from . import caching, ratelimit, resilience, telemetry

__all__ = [
    "create_cli_application",
    "main",
    "caching",
    "ratelimit",
    "resilience",
    "telemetry",
]
'''

write_file("sarathi/__init__.py", SARATHI_INIT)
write_file("src/sarathi/__init__.py", SARATHI_INIT)

print("Entry point fix completed!")
