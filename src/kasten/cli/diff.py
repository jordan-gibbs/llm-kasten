"""Diff command — show what changed since last sync."""

from __future__ import annotations

import typer

from kasten.cli._output import console, output
from kasten.models.output import error, success


def diff(
    json_output: bool = typer.Option(False, "--json", "-j", help="JSON output"),
) -> None:
    """Show what changed since the last sync."""
    from kasten.core.sync import compute_sync_plan
    from kasten.core.vault import Vault, VaultError

    try:
        vault = Vault.discover()
    except VaultError as e:
        if json_output:
            output(error(str(e), "NO_VAULT"), json_mode=True)
        else:
            console.print(f"[red]Error:[/] {e}")
        raise typer.Exit(1)

    plan = compute_sync_plan(vault)

    # Count current broken links for comparison
    broken_before = vault.db.execute(
        "SELECT COUNT(*) as c FROM links WHERE target_id IS NULL"
    ).fetchone()["c"]

    data = {
        "new": [str(p.relative_to(vault.root)) for p in plan.to_add],
        "modified": [str(p.relative_to(vault.root)) for p in plan.to_update],
        "deleted": plan.to_delete,
        "unchanged": plan.unchanged,
        "broken_links": broken_before,
    }

    if json_output:
        output(success(data, vault=str(vault.root)), json_mode=True)
    else:
        total_changes = len(plan.to_add) + len(plan.to_update) + len(plan.to_delete)
        if total_changes == 0:
            console.print("[green]No changes since last sync.[/]")
            return

        if plan.to_add:
            console.print(f"\n[green]+{len(plan.to_add)} new:[/]")
            for p in plan.to_add:
                console.print(f"  [green]+[/] {p.relative_to(vault.root)}")

        if plan.to_update:
            console.print(f"\n[yellow]~{len(plan.to_update)} modified:[/]")
            for p in plan.to_update:
                console.print(f"  [yellow]~[/] {p.relative_to(vault.root)}")

        if plan.to_delete:
            console.print(f"\n[red]-{len(plan.to_delete)} deleted:[/]")
            for p in plan.to_delete:
                console.print(f"  [red]-[/] {p}")

        console.print(f"\n[dim]={plan.unchanged} unchanged[/]")
        if broken_before > 0:
            console.print(f"[dim]{broken_before} broken links in current index[/]")
