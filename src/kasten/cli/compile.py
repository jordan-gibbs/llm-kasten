"""LLM compilation CLI commands."""

from __future__ import annotations

import typer

from kasten.cli._output import console, output
from kasten.models.output import error, success

app = typer.Typer(invoke_without_command=True)


@app.callback(invoke_without_command=True)
def compile_cmd(
    ctx: typer.Context,
    raw_id: str | None = typer.Argument(None, help="Specific raw file ID to compile"),
    all_pending: bool = typer.Option(False, "--all", "-a", help="Compile all uncompiled raw files"),
    strategy: str = typer.Option("summarize", "--strategy", "-s", help="Strategy: summarize|extract|restructure"),
    model: str | None = typer.Option(None, "--model", "-m", help="Override LLM model"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Show what would be compiled"),
    json_output: bool = typer.Option(False, "--json", "-j", help="JSON output"),
) -> None:
    """LLM-compile raw material into structured notes."""
    if ctx.invoked_subcommand is not None:
        return

    from kasten.core.vault import Vault

    vault = Vault.discover()
    vault.auto_sync()

    # Find raw notes pending compilation
    if raw_id:
        rows = vault.db.execute(
            "SELECT id, path, title FROM notes WHERE id = ? AND type = 'raw'", (raw_id,)
        ).fetchall()
    elif all_pending:
        rows = vault.db.execute(
            "SELECT id, path, title FROM notes WHERE type = 'raw' "
            "AND id NOT IN (SELECT compile_source FROM notes WHERE compile_source IS NOT NULL)"
        ).fetchall()
    else:
        if json_output:
            output(error("Specify a raw note ID or use --all", "NO_TARGET"), json_mode=True)
        else:
            console.print("[yellow]Specify a raw note ID or use --all[/]")
        raise typer.Exit(1)

    if not rows:
        if json_output:
            output(success({"compiled": []}, count=0, vault=str(vault.root)), json_mode=True)
        else:
            console.print("[dim]Nothing to compile.[/]")
        return

    if dry_run:
        items = [{"id": r["id"], "title": r["title"], "path": r["path"]} for r in rows]
        if json_output:
            output(success({"to_compile": items}, count=len(items), vault=str(vault.root)), json_mode=True)
        else:
            console.print(f"[bold]Would compile {len(items)} raw notes:[/]")
            for item in items:
                console.print(f"  [cyan]{item['id']}[/] — {item['title']}")
        return

    # Actual compilation requires LLM provider
    try:
        from kasten.compile.pipeline import CompilePipeline

        pipeline = CompilePipeline(vault, model_override=model)
        results = pipeline.compile_batch(
            [dict(r) for r in rows], strategy=strategy
        )
        if json_output:
            output(success({"compiled": results}, count=len(results), vault=str(vault.root)), json_mode=True)
        else:
            console.print(f"[green]Compiled {len(results)} notes.[/]")
            for r in results:
                console.print(f"  [cyan]{r['id']}[/] — {r['title']}")
    except ImportError:
        msg = "LLM compilation requires: pip install kasten[llm] or kasten[anthropic]"
        if json_output:
            output(error(msg, "MISSING_DEPS"), json_mode=True)
        else:
            console.print(f"[red]{msg}[/]")
        raise typer.Exit(1)
