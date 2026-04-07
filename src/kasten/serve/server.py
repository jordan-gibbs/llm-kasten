"""Lightweight HTTP server for browsing kasten vaults."""

from __future__ import annotations

import urllib.parse
from http.server import HTTPServer, BaseHTTPRequestHandler

from kasten.serve.renderer import render_markdown

CSS = """
* { margin: 0; padding: 0; box-sizing: border-box; }
body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif;
       line-height: 1.6; color: #1a1a2e; background: #fafafa; }
a { color: #3a86ff; text-decoration: none; }
a:hover { text-decoration: underline; }
.wiki-link { color: #8338ec; font-weight: 500; }
.wiki-link.broken { color: #e63946; text-decoration: line-through; }

.layout { display: flex; min-height: 100vh; }
nav { width: 240px; background: #16213e; color: #e0e0e0; padding: 1rem;
      position: fixed; height: 100vh; overflow-y: auto; }
nav a { color: #90caf9; display: block; padding: 2px 0; }
nav h3 { color: white; margin: 1rem 0 0.5rem 0; font-size: 0.85rem;
         text-transform: uppercase; letter-spacing: 0.05em; }
nav .brand { font-size: 1.2rem; font-weight: bold; color: white; margin-bottom: 1rem; }

main { margin-left: 240px; padding: 2rem 3rem; max-width: 900px; flex: 1; }
main h1 { margin-bottom: 0.5rem; }
main h2 { margin-top: 1.5rem; margin-bottom: 0.5rem; border-bottom: 1px solid #e0e0e0; padding-bottom: 0.3rem; }
main h3 { margin-top: 1rem; }

.meta { color: #666; font-size: 0.85rem; margin-bottom: 1.5rem; }
.meta .tag { background: #e8f5e9; color: #2e7d32; padding: 2px 8px; border-radius: 12px;
             font-size: 0.75rem; margin-right: 4px; }
.meta .status { background: #e3f2fd; color: #1565c0; padding: 2px 8px; border-radius: 12px;
                font-size: 0.75rem; }
.meta .status.deprecated { background: #fce4ec; color: #c62828; }
.meta .status.draft { background: #fff3e0; color: #e65100; }

.backlinks { background: #f5f5f5; border-radius: 8px; padding: 1rem; margin-top: 2rem; }
.backlinks h3 { font-size: 0.9rem; margin-bottom: 0.5rem; }
.backlinks li { font-size: 0.85rem; }

code { background: #f0f0f0; padding: 2px 6px; border-radius: 3px; font-size: 0.9em; }
pre { background: #1a1a2e; color: #e0e0e0; padding: 1rem; border-radius: 6px;
      overflow-x: auto; margin: 1rem 0; }
pre code { background: none; padding: 0; color: inherit; }

.md-table { border-collapse: collapse; margin: 1rem 0; }
.md-table th, .md-table td { border: 1px solid #ddd; padding: 8px 12px; text-align: left; }
.md-table th { background: #f5f5f5; font-weight: 600; }
.md-table tr:nth-child(even) { background: #fafafa; }

blockquote { border-left: 3px solid #3a86ff; padding-left: 1rem; color: #555; margin: 1rem 0; }
ul { margin: 0.5rem 0 0.5rem 1.5rem; }
li { margin: 0.2rem 0; }

.search-box { margin-bottom: 1rem; }
.search-box input { width: 100%; padding: 6px 10px; border: 1px solid #ccc; border-radius: 4px;
                    background: #0a1628; color: #e0e0e0; }
.results .result { margin-bottom: 1rem; }
.results .result .title { font-weight: 600; }
.results .result .snippet { color: #666; font-size: 0.85rem; }
"""


class KastenHandler(BaseHTTPRequestHandler):
    vault = None  # Set by serve()
    _db = None    # Thread-safe DB connection for the server

    @property
    def db(self):
        """Get a thread-safe DB connection (separate from vault.db)."""
        if self.__class__._db is None:
            import sqlite3
            self.__class__._db = sqlite3.connect(str(self.__class__.vault.db_path), check_same_thread=False)
            self.__class__._db.row_factory = sqlite3.Row
        return self.__class__._db

    def do_GET(self):
        import html as html_mod
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        query = urllib.parse.parse_qs(parsed.query)

        if path == "/" or path == "":
            self._serve_index()
        elif path.startswith("/note/"):
            note_id = urllib.parse.unquote(path[6:])
            self._serve_note(note_id)
        elif path.startswith("/tag/"):
            tag = urllib.parse.unquote(path[5:])
            self._serve_tag(tag)
        elif path == "/tags":
            self._serve_tags()
        elif path == "/search":
            q = query.get("q", [""])[0]
            self._serve_search(q)
        else:
            self._send(404, "<h1>Not Found</h1>")

    def _send(self, code: int, body_html: str, title: str = "kasten"):
        nav = self._build_nav()
        full = f"""<!DOCTYPE html><html><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title><style>{CSS}</style></head>
<body><div class="layout"><nav>{nav}</nav><main>{body_html}</main></div></body></html>"""
        self.send_response(code)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(full.encode("utf-8"))

    def _build_nav(self) -> str:
        vault = self.__class__.vault
        name = vault.config.name
        lines = [
            f'<div class="brand">{name}</div>',
            f'<form action="/search"><div class="search-box">'
            f'<input type="text" name="q" placeholder="Search..."></div></form>',
            '<a href="/">Home</a>',
            '<a href="/tags">Tags</a>',
            '<h3>Recent</h3>',
        ]
        rows = self.db.execute(
            "SELECT id, title FROM notes WHERE type NOT IN ('index') "
            "ORDER BY COALESCE(updated, created) DESC LIMIT 15"
        ).fetchall()
        for r in rows:
            lines.append(f'<a href="/note/{r["id"]}">{r["title"]}</a>')
        return "\n".join(lines)

    def _serve_index(self):
        import html as html_mod
        vault = self.__class__.vault
        rows = self.db.execute(
            "SELECT id, title, status, summary, word_count FROM notes "
            "WHERE type NOT IN ('index') ORDER BY title"
        ).fetchall()
        body = "<h1>All Notes</h1>\n<ul>\n"
        for r in rows:
            summary = f' — <span style="color:#666">{html_mod.escape(r["summary"] or "")}</span>' if r["summary"] else ""
            body += f'<li><a href="/note/{html_mod.escape(r["id"])}">{html_mod.escape(r["title"])}</a>{summary} '
            body += f'<span class="meta"><span class="status {r["status"]}">{html_mod.escape(r["status"])}</span></span></li>\n'
        body += "</ul>"
        self._send(200, body, "Home")

    def _serve_note(self, note_id: str):
        import html as html_mod
        vault = self.__class__.vault
        row = self.db.execute(
            "SELECT n.*, nc.body FROM notes n "
            "JOIN note_content nc ON n.id = nc.note_id WHERE n.id = ?",
            (note_id,),
        ).fetchone()
        if not row:
            self._send(404, f"<h1>Note not found: {html_mod.escape(note_id)}</h1>")
            return

        tags = [r["tag"] for r in self.db.execute("SELECT tag FROM tags WHERE note_id = ?", (note_id,))]
        backlinks = self.db.execute(
            "SELECT l.source_id, n.title FROM links l "
            "JOIN notes n ON l.source_id = n.id WHERE l.target_id = ? ORDER BY n.title",
            (note_id,),
        ).fetchall()

        # Render
        html_body = render_markdown(row["body"])
        tags_html = " ".join(f'<a href="/tag/{t}" class="tag">{t}</a>' for t in tags)
        status_class = row["status"]
        meta = (
            f'<div class="meta">'
            f'<span class="status {status_class}">{row["status"]}</span> '
            f'{tags_html} '
            f'<span>{row["word_count"]} words</span>'
            f'</div>'
        )

        bl_html = ""
        if backlinks:
            bl_items = "\n".join(
                f'<li><a href="/note/{r["source_id"]}">{r["title"]}</a></li>' for r in backlinks
            )
            bl_html = f'<div class="backlinks"><h3>Backlinks</h3><ul>{bl_items}</ul></div>'

        body = f"{meta}\n{html_body}\n{bl_html}"
        self._send(200, body, row["title"])

    def _serve_tag(self, tag: str):
        import html as html_mod
        vault = self.__class__.vault
        rows = self.db.execute(
            "SELECT n.id, n.title, n.status, n.summary FROM notes n "
            "JOIN tags t ON n.id = t.note_id WHERE t.tag = ? ORDER BY n.title",
            (tag,),
        ).fetchall()
        safe_tag = html_mod.escape(tag)
        body = f"<h1>Tag: {safe_tag}</h1>\n<p>{len(rows)} notes</p>\n<ul>\n"
        for r in rows:
            summary = f' — <span style="color:#666">{html_mod.escape(r["summary"] or "")}</span>' if r["summary"] else ""
            body += f'<li><a href="/note/{html_mod.escape(r["id"])}">{html_mod.escape(r["title"])}</a>{summary}</li>\n'
        body += "</ul>"
        self._send(200, body, f"Tag: {safe_tag}")

    def _serve_tags(self):
        vault = self.__class__.vault
        rows = self.db.execute(
            "SELECT tag, COUNT(*) as c FROM tags GROUP BY tag ORDER BY c DESC"
        ).fetchall()
        body = "<h1>All Tags</h1>\n<ul>\n"
        for r in rows:
            body += f'<li><a href="/tag/{r["tag"]}">{r["tag"]}</a> ({r["c"]} notes)</li>\n'
        body += "</ul>"
        self._send(200, body, "Tags")

    def _serve_search(self, query: str):
        import html as html_mod
        vault = self.__class__.vault
        safe_q = html_mod.escape(query)
        body = f'<h1>Search: {safe_q}</h1>\n'
        if not query:
            body += "<p>Enter a search term.</p>"
            self._send(200, body, "Search")
            return

        from kasten.search.fts import search_fts
        results = search_fts(self.db, query, limit=50)
        body += f"<p>{len(results)} results</p>\n<div class='results'>\n"
        for r in results:
            snippet = r["snippet"].replace(">>>", "<mark>").replace("<<<", "</mark>")
            body += (
                f'<div class="result"><div class="title">'
                f'<a href="/note/{r["id"]}">{r["title"]}</a></div>'
                f'<div class="snippet">{snippet}</div></div>\n'
            )
        body += "</div>"
        self._send(200, body, f"Search: {query}")

    def log_message(self, format, *args):
        # Quiet logging
        pass


def run_server(vault, port: int = 8080, open_browser: bool = False):
    """Start the HTTP server."""
    KastenHandler.vault = vault
    server = HTTPServer(("127.0.0.1", port), KastenHandler)
    url = f"http://127.0.0.1:{port}"
    print(f"Serving at {url}")
    print("Press Ctrl+C to stop.\n")

    if open_browser:
        import webbrowser
        webbrowser.open(url)

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.")
    server.server_close()
