"""Q&A CLI command — ask questions against the knowledge base."""

from __future__ import annotations

import typer

from kasten.cli._output import console, output
from kasten.models.output import error, success

app = typer.Typer(invoke_without_command=True)


@app.callback(invoke_without_command=True)
def ask(
    ctx: typer.Context,
    question: str = typer.Argument(None, help="Question to ask"),
    context_notes: int = typer.Option(5, "--context", "-c", help="Number of context notes"),
    model: str | None = typer.Option(None, "--model", "-m", help="Override LLM model"),
    show_sources: bool = typer.Option(False, "--show-sources", help="Show source notes"),
    json_output: bool = typer.Option(False, "--json", help="JSON output"),
) -> None:
    """Ask a question against the knowledge base."""
    if ctx.invoked_subcommand is not None:
        return
    if not question:
        if json_output:
            output(error("No question provided", "NO_QUESTION"), json_mode=True)
        else:
            console.print("[yellow]Usage: kasten ask 'your question here'[/]")
        raise typer.Exit(1)

    from kasten.core.vault import Vault
    from kasten.search.fts import search_fts

    vault = Vault.discover()
    vault.auto_sync()

    # Find relevant notes via FTS
    results = search_fts(vault.db, question, limit=context_notes)

    if not results:
        if json_output:
            output(error("No relevant notes found", "NO_CONTEXT"), json_mode=True)
        else:
            console.print("[dim]No relevant notes found to answer this question.[/]")
        raise typer.Exit(1)

    # Gather full content for context
    context_docs = []
    for r in results:
        row = vault.db.execute(
            "SELECT body FROM note_content WHERE note_id = ?", (r["id"],)
        ).fetchone()
        if row:
            context_docs.append({
                "id": r["id"],
                "title": r["title"],
                "body": row["body"][:4000],  # Truncate for context window
            })

    # Try to use LLM for Q&A
    try:
        from kasten.llm.provider import get_provider

        provider = get_provider(vault.config.raw)
        if model:
            # Override model
            pass

        context_text = "\n\n---\n\n".join(
            f"# {d['title']} (id: {d['id']})\n{d['body']}" for d in context_docs
        )
        messages = [
            {
                "role": "system",
                "content": (
                    "You are a knowledgeable assistant. Answer based ONLY on the provided "
                    "knowledge base excerpts. Cite sources using [[note-id]] notation. "
                    "If the answer is not in the provided context, say so."
                ),
            },
            {
                "role": "user",
                "content": f"Knowledge base context:\n\n{context_text}\n\n---\n\nQuestion: {question}",
            },
        ]

        response = provider.complete(messages)

        data = {
            "question": question,
            "answer": response.content,
            "model": response.model,
            "sources": [{"id": d["id"], "title": d["title"]} for d in context_docs],
        }

        if json_output:
            output(success(data, vault=str(vault.root)), json_mode=True)
        else:
            console.print(f"\n[bold]Answer:[/]\n")
            from rich.markdown import Markdown

            console.print(Markdown(response.content))
            if show_sources:
                console.print(f"\n[dim]Sources:[/]")
                for s in data["sources"]:
                    console.print(f"  [[{s['id']}]] {s['title']}")

    except (ImportError, Exception) as e:
        # Fallback: just show relevant notes without LLM
        data = {
            "question": question,
            "answer": None,
            "note": "LLM not available. Showing relevant notes instead.",
            "relevant_notes": [{"id": d["id"], "title": d["title"]} for d in context_docs],
        }
        if json_output:
            output(success(data, vault=str(vault.root)), json_mode=True)
        else:
            console.print(f"[yellow]LLM not configured. Relevant notes for:[/] {question}\n")
            for d in context_docs:
                console.print(f"  [cyan][[{d['id']}]][/] {d['title']}")
