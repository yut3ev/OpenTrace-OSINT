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
    name: Annotated[
        str | None, typer.Option("--name", "-n", help="Target person name to investigate.")
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
    pivot: Annotated[
        bool,
        typer.Option("--pivot", help="Enable recursive pivoting on discovered entities."),
    ] = False,
    pivot_depth: Annotated[
        int,
        typer.Option("--pivot-depth", help="Maximum recursion depth for pivoting (1-3)."),
    ] = 1,
    pivot_budget: Annotated[
        int,
        typer.Option("--pivot-budget", help="Maximum entity budget to pivot per layer."),
    ] = 5,
    as_json: Annotated[
        bool,
        typer.Option("--json", help="Output raw JSON instead of human-readable tables."),
    ] = False,
) -> None:
    """Run an investigation against public sources for username, email, phone, or name."""
    if not any([username, email, phone, name]):
        err_console.print(
            "[bold red]Error (exit 2):[/bold red] At least one of --username, --email, --phone, or --name must be specified."
        )
        raise typer.Exit(code=2)

    orchestrator = _get_orchestrator()
    req = InvestigationRequest(
        username=username,
        email=email,
        phone=phone,
        name=name,
        modules=modules,
        max_runtime_seconds=max_runtime,
        enable_pivot=pivot,
        max_pivot_depth=pivot_depth,
        max_pivot_budget=pivot_budget,
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
    metrics = response.summary.metrics
    metrics_str = (
        f"[bold]Sources:[/bold] {metrics.registered} registered | {metrics.eligible} eligible | {metrics.attempted} attempted\n"
        f"[bold]Source Results:[/bold] {metrics.succeeded} succeeded, {metrics.no_match} no match, "
        f"{metrics.rate_limited} rate limited, {metrics.blocked} blocked, {metrics.error} errors"
    )
    console.print(
        Panel(
            f"[bold]ID:[/bold] {response.id}\n"
            f"[bold]Status:[/bold] [{status_style}]{response.status.value.upper()}[/{status_style}]\n"
            f"[bold]Duration:[/bold] {response.summary.duration_seconds}s\n"
            f"[bold]Total Findings:[/bold] {response.summary.total}\n"
            f"{metrics_str}",
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


@app.command("sources")
def list_sources_cmd(
    status: Annotated[
        str | None,
        typer.Option(
            "--status", "-s", help="Filter by manifest status (e.g. implemented, planned, tested)"
        ),
    ] = None,
    category: Annotated[
        str | None,
        typer.Option(
            "--category",
            "-c",
            help="Filter by category (developer, social, gaming, academic, etc.)",
        ),
    ] = None,
    target: Annotated[
        str | None,
        typer.Option("--target", "-t", help="Filter by target type (username, email, phone, name)"),
    ] = None,
    as_json: Annotated[bool, typer.Option("--json", help="Output as JSON.")] = False,
) -> None:
    """Browse the full source registry and manifest coverage."""
    from opentrace.modules.manifest import load_manifest

    sources = load_manifest()
    reg = get_default_registry()
    active_ids = {m.metadata.id for m in reg.list_all()}

    if status:
        sources = [s for s in sources if s.status.lower() == status.lower()]
    if category:
        sources = [s for s in sources if s.category.lower() == category.lower()]
    if target:
        sources = [s for s in sources if s.target_type.lower() == target.lower()]

    if as_json:
        data = [
            {
                "id": s.id,
                "name": s.name,
                "category": s.category,
                "target_type": s.target_type,
                "access_type": s.access_type,
                "status": s.status,
                "source_url": s.source_url,
                "is_active": s.id in active_ids,
                "description": s.description,
            }
            for s in sources
        ]
        console.print(json.dumps(data, indent=2))
        return

    table = Table(title=f"Source Catalog ({len(sources)} sources)", show_lines=True)
    table.add_column("Source ID", style="bold cyan")
    table.add_column("Name")
    table.add_column("Category", style="magenta")
    table.add_column("Target", style="blue")
    table.add_column("Access", style="dim")
    table.add_column("Status")
    table.add_column("Active", justify="center")

    for s in sources:
        is_act = s.id in active_ids
        act_badge = "[bold green]YES[/bold green]" if is_act else "[dim]NO[/dim]"
        status_color = (
            "green"
            if s.status == "implemented"
            else (
                "cyan"
                if s.status == "tested"
                else ("yellow" if s.status == "requires_api_key" else "dim")
            )
        )
        table.add_row(
            s.id,
            s.name,
            s.category,
            s.target_type,
            s.access_type,
            f"[{status_color}]{s.status}[/{status_color}]",
            act_badge,
        )

    console.print(table)


@app.command("stats")
def stats_cmd(
    as_json: Annotated[bool, typer.Option("--json", help="Output stats as JSON.")] = False,
) -> None:
    """Display platform-wide statistics, investigations, and source metrics."""
    from opentrace.modules.manifest import load_manifest

    orchestrator = _get_orchestrator()
    investigations = asyncio.run(orchestrator.storage.list_investigations(limit=1000))
    total_findings = sum(len(inv.get("findings", [])) for inv in investigations)

    manifest_sources = load_manifest()
    reg = get_default_registry()
    active_count = len(reg.list_all())

    by_status: dict[str, int] = {}
    for s in manifest_sources:
        by_status[s.status] = by_status.get(s.status, 0) + 1

    if as_json:
        data = {
            "total_investigations": len(investigations),
            "total_findings": total_findings,
            "manifest_sources": len(manifest_sources),
            "active_modules": active_count,
            "sources_by_status": by_status,
        }
        console.print(json.dumps(data, indent=2))
        return

    console.print(
        Panel(
            f"[bold]Total Investigations:[/bold] {len(investigations)}\n"
            f"[bold]Total Findings Captured:[/bold] {total_findings}\n"
            f"[bold]Total Catalog Sources:[/bold] {len(manifest_sources)}\n"
            f"[bold]Active Running Modules:[/bold] {active_count}\n"
            f"[bold]Catalog Breakdown:[/bold] {', '.join(f'{k}: {v}' for k, v in by_status.items())}",
            title="[bold cyan]OpenTrace Platform Statistics[/bold cyan]",
        )
    )


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


@app.command("validate-sources")
def validate_sources_cmd(
    live: Annotated[
        bool,
        typer.Option(
            "--live", help="Test live network connectivity against real public endpoints."
        ),
    ] = False,
    target_type: Annotated[
        str | None,
        typer.Option(
            "--target-type", "-t", help="Filter by target type: username, email, phone, name."
        ),
    ] = None,
    category: Annotated[
        str | None,
        typer.Option("--category", "-c", help="Filter by source category."),
    ] = None,
    as_json: Annotated[
        bool,
        typer.Option("--json", help="Output validation results as raw JSON."),
    ] = False,
) -> None:
    """Validate registered source adapters against deterministic fixtures or live endpoints."""
    from opentrace.core.validator import validate_all_modules

    mode_label = (
        "[bold red]LIVE INTEGRATION[/bold red]"
        if live
        else "[bold cyan]DETERMINISTIC FIXTURE[/bold cyan]"
    )
    console.print(f"Running source adapter validation in {mode_label} mode...\n")

    results = asyncio.run(
        validate_all_modules(live=live, target_type=target_type, category=category)
    )

    if as_json:
        out = [
            {
                "module_id": r.module_id,
                "source_name": r.source_name,
                "target_type": r.target_type,
                "category": r.category,
                "mode": r.mode,
                "passed": r.passed,
                "status": r.status,
                "finding_count": r.finding_count,
                "duration_ms": r.duration_ms,
                "message": r.message,
            }
            for r in results
        ]
        console.print(json.dumps(out, indent=2))
        return

    table = Table(title=f"Source Adapter Validation ({len(results)} sources checked)")
    table.add_column("Module ID", style="cyan", no_wrap=True)
    table.add_column("Source Name", style="bold")
    table.add_column("Type", style="magenta")
    table.add_column("Category", style="blue")
    table.add_column("Status", style="yellow")
    table.add_column("Duration", justify="right")
    table.add_column("Result", style="bold")

    passed_count = sum(1 for r in results if r.passed)
    failed_count = len(results) - passed_count

    for r in results:
        res_style = "green" if r.passed else "red"
        res_text = f"[{res_style}]{'PASS' if r.passed else 'FAIL'}[/{res_style}]"
        table.add_row(
            r.module_id,
            r.source_name,
            r.target_type,
            r.category,
            r.status,
            f"{r.duration_ms:.1f}ms",
            res_text,
        )

    console.print(table)
    summary_color = "green" if failed_count == 0 else "red"
    console.print(
        f"\n[{summary_color}]Validation complete:[/{summary_color}] {passed_count} passed, {failed_count} failed out of {len(results)} adapters."
    )
    if failed_count > 0:
        raise typer.Exit(code=1)


if __name__ == "__main__":
    app()
