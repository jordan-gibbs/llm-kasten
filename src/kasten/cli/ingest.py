"""Ingest CLI commands — bring source material into the vault."""

from __future__ import annotations

from pathlib import Path

import typer

from kasten.cli._output import console, output
from kasten.models.output import error, success

app = typer.Typer()


@app.command("file")
def ingest_file(
    path: str = typer.Argument(..., help="Path to file to ingest"),
    title: str | None = typer.Option(None, "--title", "-T", help="Override title"),
    tags: list[str] = typer.Option([], "--tag", "-t", help="Tags"),
    do_compile: bool = typer.Option(False, "--compile", help="Compile after ingest"),
    json_output: bool = typer.Option(False, "--json", "-j", help="JSON output"),
) -> None:
    """Ingest a local file as a raw note."""
    from kasten.core.vault import Vault
    from kasten.ingest.file import ingest_local_file

    vault = Vault.discover()
    result = ingest_local_file(vault, Path(path), title=title, tags=tags)

    if json_output:
        output(success(result, vault=str(vault.root)), json_mode=True)
    else:
        console.print(f"[green]Ingested:[/] {result['raw_path']}")


@app.command("web")
def ingest_web(
    url: str = typer.Argument(..., help="URL to ingest"),
    title: str | None = typer.Option(None, "--title", "-T", help="Override title"),
    tags: list[str] = typer.Option([], "--tag", "-t", help="Tags"),
    do_compile: bool = typer.Option(False, "--compile", help="Compile after ingest"),
    json_output: bool = typer.Option(False, "--json", "-j", help="JSON output"),
) -> None:
    """Ingest a web page as a raw note."""
    try:
        from kasten.ingest.web import ingest_url
    except ImportError:
        msg = "Web ingestion requires: pip install kasten[web]"
        if json_output:
            output(error(msg, "MISSING_DEPS"), json_mode=True)
        else:
            console.print(f"[red]{msg}[/]")
        raise typer.Exit(1)

    from kasten.core.vault import Vault

    vault = Vault.discover()
    result = ingest_url(vault, url, title=title, tags=tags)

    if json_output:
        output(success(result, vault=str(vault.root)), json_mode=True)
    else:
        console.print(f"[green]Ingested:[/] {result['raw_path']}")


@app.command("pdf")
def ingest_pdf(
    path: str = typer.Argument(..., help="Path to PDF"),
    title: str | None = typer.Option(None, "--title", "-T", help="Override title"),
    tags: list[str] = typer.Option([], "--tag", "-t", help="Tags"),
    pages: str | None = typer.Option(None, "--pages", help="Page range, e.g. '1-5,10'"),
    do_compile: bool = typer.Option(False, "--compile", help="Compile after ingest"),
    json_output: bool = typer.Option(False, "--json", "-j", help="JSON output"),
) -> None:
    """Ingest a PDF as a raw note."""
    try:
        from kasten.ingest.pdf import ingest_pdf_file
    except ImportError:
        msg = "PDF ingestion requires: pip install kasten[pdf]"
        if json_output:
            output(error(msg, "MISSING_DEPS"), json_mode=True)
        else:
            console.print(f"[red]{msg}[/]")
        raise typer.Exit(1)

    from kasten.core.vault import Vault

    vault = Vault.discover()
    result = ingest_pdf_file(vault, Path(path), title=title, tags=tags, pages=pages)

    if json_output:
        output(success(result, vault=str(vault.root)), json_mode=True)
    else:
        console.print(f"[green]Ingested:[/] {result['raw_path']}")


@app.command("list")
def ingest_list(
    status_filter: str | None = typer.Option(None, "--status", "-s", help="Filter: raw|compiled|failed"),
    json_output: bool = typer.Option(False, "--json", "-j", help="JSON output"),
) -> None:
    """Show ingestion log."""
    from kasten.core.vault import Vault

    vault = Vault.discover()
    sql = "SELECT * FROM ingest_log"
    params: list = []
    if status_filter:
        sql += " WHERE status = ?"
        params.append(status_filter)
    sql += " ORDER BY ingested_at DESC"

    rows = vault.db.execute(sql, params).fetchall()
    items = [dict(r) for r in rows]

    if json_output:
        output(success(items, count=len(items), vault=str(vault.root)), json_mode=True)
    else:
        from rich.table import Table

        table = Table(title="Ingest Log", show_header=True, header_style="bold")
        table.add_column("ID", style="dim")
        table.add_column("Type")
        table.add_column("Path", style="cyan")
        table.add_column("Status", style="yellow")
        table.add_column("Ingested At", style="dim")
        for item in items:
            table.add_row(
                str(item["id"]),
                item["source_type"],
                item["raw_path"],
                item["status"],
                item["ingested_at"],
            )
        console.print(table)
