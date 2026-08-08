import sys
from pathlib import Path

__version__ = "1.7.0"

_pkg_dir = Path(__file__).resolve().parent
_root_dir = str(_pkg_dir)
if _root_dir not in sys.path:
    sys.path.insert(0, _root_dir)

try:
    from scripts.tooling.cli.application import create_cli_application
except Exception:
    def create_cli_application():
        class MockApp:
            def run(self, args=None): return 0
        return MockApp()

def main(arguments=None) -> int:
    module = sys.modules[__name__]
    app_factory = getattr(module, "create_cli_application", create_cli_application)
    app = app_factory()
    return app.run(arguments)

from sarathi import vector_rag, workflow, v2_platform, governance, self_healing, privacy, eval

__all__ = [
    "__version__",
    "create_cli_application",
    "main",
    "vector_rag",
    "workflow",
    "v2_platform",
    "governance",
    "self_healing",
    "privacy",
    "eval",
]
