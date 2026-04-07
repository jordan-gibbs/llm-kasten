"""Kasten CLI — main typer application."""

import typer

from kasten import __version__


def _version_callback(value: bool) -> None:
    if value:
        typer.echo(f"kasten v{__version__}")
        raise typer.Exit()


app = typer.Typer(
    name="kasten",
    help="LLM-powered personal knowledge base manager.",
    no_args_is_help=True,
    rich_markup_mode="rich",
)


@app.callback()
def main(
    version: bool = typer.Option(False, "--version", "-V", callback=_version_callback, is_eager=True, help="Show version"),
) -> None:
    pass


# Root-level commands
from kasten.cli.main import init as _init, status as _status, sync as _sync  # noqa: E402
from kasten.cli.search import search as _search  # noqa: E402
from kasten.cli.dedup import dedup as _dedup  # noqa: E402
from kasten.cli.import_cmd import import_vault as _import  # noqa: E402
from kasten.cli.watch import watch as _watch  # noqa: E402
from kasten.cli.serve import serve as _serve  # noqa: E402
from kasten.cli.repair import repair as _repair  # noqa: E402
from kasten.cli.note import note_tags as _tags, note_show as _show  # noqa: E402

app.command("init")(_init)
app.command("status")(_status)
app.command("sync")(_sync)
app.command("search")(_search)
app.command("tags")(_tags)
app.command("show", hidden=True)(_show)
app.command("dedup")(_dedup)
app.command("import")(_import)
app.command("repair")(_repair)
app.command("watch")(_watch)
app.command("serve")(_serve)

# Sub-apps
from kasten.cli.note import app as note_app  # noqa: E402
from kasten.cli.graph import app as graph_app  # noqa: E402
from kasten.cli.ingest import app as ingest_app  # noqa: E402
from kasten.cli.index import app as index_app  # noqa: E402
from kasten.cli.lint import app as lint_app  # noqa: E402
from kasten.cli.export import app as export_app  # noqa: E402
from kasten.cli.compile import app as compile_app  # noqa: E402
from kasten.cli.ask import app as ask_app  # noqa: E402
from kasten.cli.config_cmd import app as config_app  # noqa: E402
from kasten.cli.topic import app as topic_app  # noqa: E402
from kasten.cli.batch import app as batch_app  # noqa: E402
from kasten.cli.template import app as template_app  # noqa: E402
from kasten.cli.git_cmd import app as git_app  # noqa: E402
from kasten.cli.tag import app as tag_app  # noqa: E402

app.add_typer(note_app, name="note", help="Note CRUD operations.")
app.add_typer(graph_app, name="graph", help="Knowledge graph and link analysis.")
app.add_typer(ingest_app, name="ingest", help="Ingest files, URLs, or PDFs.")
app.add_typer(index_app, name="index", help="Auto-generated index pages.")
app.add_typer(lint_app, name="lint", help="Health-check the vault.")
app.add_typer(export_app, name="export", help="Export notes.")
app.add_typer(compile_app, name="compile", help="LLM-compile raw notes.")
app.add_typer(ask_app, name="ask", help="Q&A against the knowledge base.")
app.add_typer(config_app, name="config", help="Configuration.")
app.add_typer(topic_app, name="topic", help="Topic hierarchy.")
app.add_typer(batch_app, name="batch", help="Bulk operations.")
app.add_typer(template_app, name="template", help="Note templates.")
app.add_typer(git_app, name="git", help="Git integration.")
app.add_typer(tag_app, name="tag", help="Tag management.")
