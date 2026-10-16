"""OpenTrace command-line interface powered by Typer and Rich."""

from __future__ import annotations

import asyncio
import json
from typing import Annotated

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

import opentrace
from opentrace.api.schemas.investigation import InvestigationRequest
from opentrace.config import get_settings
from opentrace.core.orchestrator import InvestigationOrchestrator
from opentrace.modules.registry import get_default_registry
from opentrace.reports.csv_report import export_csv
from opentrace.reports.html_report import export_html
from opentrace.reports.json_report import export_json
from opentrace.storage.memory import MemoryStorage
from opentrace.storage.sqlite import SQLiteStorage

app = typer.Typer(
    name="opentrace",
    help="OpenTrace OSINT — Evidence-first public digital-footprint investigation CLI.",
    add_completion=False,
)
console = Console()
err_console = Console(stderr=True)


def _get_orchestrator() -> InvestigationOrchestrator:
    settings = get_settings()
    storage = (
        SQLiteStorage(settings.sqlite_path)
        if settings.storage_mode == "sqlite"
        else MemoryStorage()
    )
    return InvestigationOrchestrator(storage=storage, settings=settings)


def version_callback(value: bool) -> None:
    if value:
        console.print(
            f"[bold cyan]OpenTrace OSINT[/bold cyan] version [bold green]{opentrace.__version__}[/bold green]"
        )
        raise typer.Exit()


@app.callback()
def main(
    version: Annotated[
        bool | None,
        typer.Option(
            "--version",
            "-v",
            callback=version_callback,
            is_eager=True,
            help="Show version and exit.",
        ),
    ] = None,
) -> None:
    pass


@app.command("investigate")
def investigate_cmd(
    username: Annotated[
        str | None, typer.Option("--username", "-u", help="Target username to investigate.")
    ] = None,
    email: Annotated[
        str | None, typer.Option("--email", "-e", help="Target email address to investigate.")
    ] = None,
    phone: Annotated[
        str | None, typer.Option("--phone", "-p", help="Target phone number to investigate.")
    ] = None,
    modules: Annotated[
        list[str] | None,
        typer.Option(
            "--module", "-m", help="Specific module ID to run. Can be specified multiple times."
        ),
    ] = None,
    max_runtime: Annotated[
        float | None,
        typer.Option("--max-runtime", help="Maximum runtime in seconds."),
    ] = None,
    as_json: Annotated[
        bool,
        typer.Option("--json", help="Output raw JSON instead of human-readable tables."),
    ] = False,
) -> None:
    """Run an investigation against public sources for username, email, or phone."""
    if not any([username, email, phone]):
        err_console.print(
            "[bold red]Error (exit 2):[/bold red] At least one of --username, --email, or --phone must be specified."
        )
        raise typer.Exit(code=2)

    orchestrator = _get_orchestrator()
    req = InvestigationRequest(
        username=username,
        email=email,
        phone=phone,
        modules=modules,
        max_runtime_seconds=max_runtime,
    )

    try:
        response = asyncio.run(orchestrator.run_investigation(req))
    except Exception as exc:
        err_console.print(f"[bold red]Investigation execution error:[/bold red] {exc}")
        raise typer.Exit(code=1) from None

    resp_dict = response.model_dump()

    if as_json:
        console.print(json.dumps(resp_dict, default=str, indent=2))
        if response.status.value == "failed":
            raise typer.Exit(code=1)
        return

    # Rich human-readable display
    status_style = (
        "green"
        if response.status.value == "completed"
        else "yellow"
        if response.status.value == "partial"
        else "red"
    )
    console.print(
        Panel(
            f"[bold]ID:[/bold] {response.id}\n"
            f"[bold]Status:[/bold] [{status_style}]{response.status.value.upper()}[/{status_style}]\n"
            f"[bold]Duration:[/bold] {response.summary.duration_seconds}s\n"
            f"[bold]Total Findings:[/bold] {response.summary.total}",
            title="[bold cyan]OpenTrace Investigation Summary[/bold cyan]",
            border_style=status_style,
        )
    )

    if response.warnings:
        for w in response.warnings:
            console.print(f"[bold yellow]Warning:[/bold yellow] {w}")

    # Findings Table
    table = Table(title="Investigation Findings", show_lines=True)
    table.add_column("Status", style="bold", width=12)
    table.add_column("Module", style="dim", width=16)
    table.add_column("Title & Evidence")
    table.add_column("Source URL", style="blue")
    table.add_column("Confidence", width=10)

    status_colors = {
        "found": "green",
        "not_found": "dim",
        "unknown": "yellow",
        "info": "cyan",
        "error": "red",
    }

    for f in response.findings:
        color = status_colors.get(f.status.value, "white")
        table.add_row(
            f"[{color}]{f.status.value.upper()}[/{color}]",
            f.module_id,
            f"[bold]{f.title}[/bold]\n{f.evidence}",
            f.source_url or "-",
            f.confidence.value,
        )

    console.print(table)

    if response.status.value == "failed":
        raise typer.Exit(code=1)


@app.command("modules")
def list_modules_cmd(
    as_json: Annotated[
        bool,
        typer.Option("--json", help="Output module definitions as JSON."),
    ] = False,
) -> None:
    """List all registered OSINT modules and capabilities."""
    reg = get_default_registry()
    modules = reg.list_all()

    if as_json:
        data = [
            {
                "id": m.metadata.id,
                "name": m.metadata.name,
                "version": m.metadata.version,
                "targets": [t.value for t in m.metadata.supported_targets],
                "enabled": m.metadata.enabled,
                "status": m.metadata.implementation_status,
                "source": m.metadata.source_name,
                "limitations": m.metadata.limitations,
            }
            for m in modules
        ]
        console.print(json.dumps(data, indent=2))
        return

    table = Table(title="Registered OSINT Modules", show_lines=True)
    table.add_column("Module ID", style="bold cyan")
    table.add_column("Name")
    table.add_column("Targets", style="magenta")
    table.add_column("Status", style="green")
    table.add_column("Description")

    for m in modules:
        meta = m.metadata
        targets = ", ".join(t.value for t in meta.supported_targets)
        status_color = "green" if meta.implementation_status == "implemented" else "yellow"
        table.add_row(
            meta.id,
            meta.name,
            targets,
            f"[{status_color}]{meta.implementation_status}[/{status_color}]",
            meta.description,
        )

    console.print(table)


@app.command("show")
def show_cmd(
    investigation_id: Annotated[str, typer.Argument(help="UUID of the investigation to display.")],
    as_json: Annotated[
        bool, typer.Option("--json", help="Output investigation as raw JSON.")
    ] = False,
) -> None:
    """Display the details and findings of a previous investigation."""
    orchestrator = _get_orchestrator()
    record = asyncio.run(orchestrator.storage.get_investigation(investigation_id))
    if not record:
        err_console.print(
            f"[bold red]Error:[/bold red] Investigation '{investigation_id}' not found."
        )
        raise typer.Exit(code=1)

    if as_json:
        console.print(json.dumps(record, default=str, indent=2))
        return

    status = record.get("status", "unknown")
    console.print(
        Panel(
            f"[bold]ID:[/bold] {record.get('id')}\n"
            f"[bold]Status:[/bold] {status.upper()}\n"
            f"[bold]Created:[/bold] {record.get('created_at')}\n"
            f"[bold]Completed:[/bold] {record.get('completed_at')}",
            title="[bold cyan]Investigation Record[/bold cyan]",
        )
    )

    findings = record.get("findings", [])
    table = Table(title=f"Findings ({len(findings)})", show_lines=True)
    table.add_column("Status", width=12)
    table.add_column("Module", width=16)
    table.add_column("Title & Evidence")
    table.add_column("Confidence", width=10)

    for f in findings:
        st = f.get("status", "unknown")
        table.add_row(
            st.upper(),
            f.get("module_id", ""),
            f"[bold]{f.get('title', '')}[/bold]\n{f.get('evidence', '')}",
            f.get("confidence", ""),
        )

    console.print(table)


@app.command("delete")
def delete_cmd(
    investigation_id: Annotated[str, typer.Argument(help="UUID of the investigation to delete.")],
) -> None:
    """Delete an investigation record from the configured storage backend."""
    orchestrator = _get_orchestrator()
    deleted = asyncio.run(orchestrator.storage.delete_investigation(investigation_id))
    if not deleted:
        err_console.print(
            f"[bold red]Error:[/bold red] Investigation '{investigation_id}' not found."
        )
        raise typer.Exit(code=1)
    console.print(
        f"[bold green]Successfully deleted investigation:[/bold green] {investigation_id}"
    )


@app.command("export")
def export_cmd(
    investigation_id: Annotated[str, typer.Argument(help="UUID of the investigation to export.")],
    format: Annotated[
        str, typer.Option("--format", "-f", help="Export format: json, csv, or html.")
    ] = "json",
    output: Annotated[
        str | None, typer.Option("--output", "-o", help="Target output file path.")
    ] = None,
) -> None:
    """Export investigation findings into JSON, CSV, or HTML format."""
    orchestrator = _get_orchestrator()
    record = asyncio.run(orchestrator.storage.get_investigation(investigation_id))
    if not record:
        err_console.print(
            f"[bold red]Error:[/bold red] Investigation '{investigation_id}' not found."
        )
        raise typer.Exit(code=1)

    fmt = format.lower()
    if fmt == "json":
        result = export_json(record)
    elif fmt == "csv":
        result = export_csv(record)
    elif fmt == "html":
        result = export_html(record)
    else:
        err_console.print(
            f"[bold red]Error (exit 2):[/bold red] Invalid format '{format}'. Choose from: json, csv, html."
        )
        raise typer.Exit(code=2)

    if output:
        try:
            with open(output, "w", encoding="utf-8") as f:
                f.write(result)
            console.print(f"[bold green]Report exported successfully to:[/bold green] {output}")
        except Exception as exc:
            err_console.print(f"[bold red]Failed to write export file:[/bold red] {exc}")
            raise typer.Exit(code=1) from None
    else:
        console.print(result)


if __name__ == "__main__":
    app()
