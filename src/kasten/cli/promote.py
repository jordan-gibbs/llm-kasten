"""Auto-promote notes through the status lifecycle based on quality criteria."""

from __future__ import annotations

from datetime import UTC

import typer

from kasten.cli._output import console, output
from kasten.models.output import success


def promote(
    dry_run: bool = typer.Option(False, "--dry-run", help="Preview what would be promoted"),
    min_words: int = typer.Option(50, "--min-words", help="Minimum words for promotion"),
    json_output: bool = typer.Option(False, "--json", "-j", help="JSON output"),
) -> None:
    """Auto-promote draft notes that meet quality criteria to 'review' or 'evergreen'.

    Criteria for draft -> review: has summary, has tags, has 50+ words.
    Criteria for review -> evergreen: has links (in or out), has 100+ words.
    """
    from datetime import datetime

    from kasten.core.frontmatter import parse_frontmatter, serialize_frontmatter
    from kasten.core.vault import Vault, VaultError

    try:
        vault = Vault.discover()
    except VaultError as e:
        if json_output:
            output({"ok": False, "error": str(e)}, json_mode=True)
        else:
            console.print(f"[red]Error:[/] {e}")
        raise typer.Exit(1)

    vault.auto_sync()
    conn = vault.db

    promotions = []

    # Draft -> Review: has summary, has tags, has min_words
    drafts = conn.execute("""
        SELECT n.id, n.path, n.title, n.word_count, n.summary
        FROM notes n
        WHERE n.status = 'draft' AND n.type NOT IN ('index')
          AND n.word_count >= ?
          AND n.summary IS NOT NULL AND LENGTH(n.summary) > 0
          AND n.id IN (SELECT note_id FROM tags)
    """, (min_words,)).fetchall()

    for row in drafts:
        promotions.append({
            "id": row["id"],
            "title": row["title"],
            "from": "draft",
            "to": "review",
            "reason": f"{row['word_count']}w, has summary, has tags",
        })

    # Review -> Evergreen: has links (in or out), has 100+ words
    reviews = conn.execute("""
        SELECT n.id, n.path, n.title, n.word_count
        FROM notes n
        WHERE n.status = 'review' AND n.type NOT IN ('index')
          AND n.word_count >= 100
          AND (n.id IN (SELECT DISTINCT source_id FROM links)
               OR n.id IN (SELECT DISTINCT target_id FROM links WHERE target_id IS NOT NULL))
    """).fetchall()

    for row in reviews:
        promotions.append({
            "id": row["id"],
            "title": row["title"],
            "from": "review",
            "to": "evergreen",
            "reason": f"{row['word_count']}w, has links",
        })

    if dry_run or not promotions:
        if json_output:
            action = "would_promote" if dry_run else "promotions"
            output(success({action: promotions}, count=len(promotions), vault=str(vault.root)), json_mode=True)
        else:
            if not promotions:
                console.print("[dim]No notes ready for promotion.[/]")
            else:
                console.print(f"[bold]Would promote {len(promotions)} notes:[/]")
                for p in promotions:
                    console.print(f"  [cyan]{p['id']}[/] {p['from']} -> {p['to']} ({p['reason']})")
        return

    # Apply promotions
    errors = []
    for p in promotions:
        try:
            row = conn.execute("SELECT path FROM notes WHERE id = ?", (p["id"],)).fetchone()
            if not row:
                continue
            file_path = vault.root / row["path"]
            content = file_path.read_text(encoding="utf-8-sig")
            meta, body = parse_frontmatter(content)
            meta.status = p["to"]
            meta.updated = datetime.now(UTC)
            file_path.write_text(serialize_frontmatter(meta) + "\n" + body, encoding="utf-8")
        except Exception as e:
            errors.append({"id": p["id"], "error": str(e)})

    from kasten.core.sync import compute_sync_plan, execute_sync
    plan = compute_sync_plan(vault)
    execute_sync(vault, plan)

    if json_output:
        output(success({"promoted": promotions, "errors": errors}, count=len(promotions),
                        vault=str(vault.root)), json_mode=True)
    else:
        console.print(f"[green]Promoted {len(promotions)} notes:[/]")
        for p in promotions:
            console.print(f"  [cyan]{p['id']}[/] {p['from']} -> {p['to']}")
        if errors:
            for e in errors:
                console.print(f"  [red]Error:[/] {e['id']}: {e['error']}")
