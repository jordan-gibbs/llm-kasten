"""Search CLI — full-text search across all notes."""

from __future__ import annotations

import typer

from kasten.cli._output import console, output
from kasten.models.output import error, success


def search(
    query: str = typer.Argument(..., help="Search query"),
    tag: list[str] = typer.Option([], "--tag", "-t", help="Filter by tag (AND logic)"),
    status: str | None = typer.Option(None, "--status", "-s", help="Filter by status"),
    note_type: str | None = typer.Option(None, "--type", help="Filter by type"),
    parent: str | None = typer.Option(None, "--parent", "-p", help="Filter by parent topic"),
    after: str | None = typer.Option(None, "--after", help="Created after date (YYYY-MM-DD)"),
    before: str | None = typer.Option(None, "--before", help="Created before date (YYYY-MM-DD)"),
    path_glob: str | None = typer.Option(None, "--path", help="Glob filter on path"),
    min_words: int | None = typer.Option(None, "--min-words", help="Minimum word count"),
    max_words: int | None = typer.Option(None, "--max-words", help="Maximum word count"),
    include_body: bool = typer.Option(False, "--include-body", help="Include full note body in results"),
    limit: int = typer.Option(20, "--limit", "-l", help="Max results"),
    offset: int = typer.Option(0, "--offset", help="Offset for pagination"),
    json_output: bool = typer.Option(False, "--json", help="JSON output"),
) -> None:
    """Full-text search across all notes."""
    from kasten.search.fts import search_fts
    from kasten.search.filters import SearchFilters
    from kasten.core.vault import Vault, VaultError

    try:
        vault = Vault.discover()
    except VaultError as e:
        if json_output:
            output(error(str(e), "NO_VAULT"), json_mode=True)
        else:
            console.print(f"[red]Error:[/] {e}")
        raise typer.Exit(1)
    vault.auto_sync()

    filters = SearchFilters(
        tags=tag or None,
        status=status,
        note_type=note_type,
        parent=parent,
        after=after,
        before=before,
        path_glob=path_glob,
        min_words=min_words,
        max_words=max_words,
    )

    ranking = {
        "boost_evergreen": vault.config.search_boost_evergreen,
        "penalize_deprecated": vault.config.search_penalize_deprecated,
        "penalize_stale": vault.config.search_penalize_stale,
    }
    results = search_fts(vault.db, query, filters=filters, limit=limit, offset=offset, ranking=ranking)

    if include_body and results:
        for r in results:
            row = vault.db.execute(
                "SELECT body FROM note_content WHERE note_id = ?", (r["id"],)
            ).fetchone()
            r["body"] = row["body"] if row else ""

    if json_output:
        output(
            success(
                {"query": query, "results": results, "total": len(results)},
                count=len(results),
                vault=str(vault.root),
            ),
            json_mode=True,
        )
    else:
        if not results:
            console.print("[dim]No results found.[/]")
            return
        for r in results:
            tags_str = ", ".join(r.get("tags", []))
            console.print(
                f"  [cyan]{r['id']}[/] [bold]{r['title']}[/] "
                f"[dim]({r['status']})[/] [green]{tags_str}[/]"
            )
            if r.get("snippet"):
                console.print(f"    [dim]{r['snippet'][:200]}[/]")
            console.print()
