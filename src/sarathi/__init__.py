import sys
from pathlib import Path

__version__ = "1.7.0"

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

from . import caching, ratelimit, resilience, telemetry, security, gateway, hardening, sdk, lts, cloud, multitenancy, cqrs, platform, edge, ai

__all__ = [
    "__version__",
    "create_cli_application",
    "main",
    "caching",
    "ratelimit",
    "resilience",
    "telemetry",
    "security",
    "gateway",
    "hardening",
    "sdk",
    "lts",
    "cloud",
    "multitenancy",
    "cqrs",
    "platform",
    "edge",
    "ai",
]
