from rich.console import Console
from rich.panel import Panel
from rich import print

console = Console()

console.print(
    Panel.fit(
        "[bold green]PROJECT SARATHI[/bold green]\n"
        "National Circular Bioeconomy Infrastructure\n"
        "Dossier Generation Platform",
        title="Version 1.0",
    )
)

print("[cyan]System Boot Successful[/cyan]")
