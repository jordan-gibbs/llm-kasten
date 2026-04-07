"""LLM compilation pipeline — transforms raw material into structured wiki notes."""

from __future__ import annotations

from datetime import datetime, timezone

from kasten.compile.prompts import get_compile_prompt
from kasten.core.frontmatter import parse_frontmatter
from kasten.core.note import write_note
from kasten.llm.provider import get_provider


class CompilePipeline:
    def __init__(self, vault, model_override: str | None = None) -> None:
        self.vault = vault
        self.provider = get_provider(vault.config.raw)
        if model_override:
            self.provider.model = model_override

    def compile_batch(self, raw_notes: list[dict], strategy: str = "summarize") -> list[dict]:
        """Compile a batch of raw notes into structured notes."""
        results = []
        for raw in raw_notes:
            try:
                result = self._compile_single(raw, strategy)
                results.append(result)
            except Exception as e:
                results.append({"id": raw["id"], "error": str(e)})
        return results

    def _compile_single(self, raw: dict, strategy: str) -> dict:
        """Compile a single raw note."""
        # Read the raw note content
        raw_path = self.vault.root / raw["path"]
        content = raw_path.read_text(encoding="utf-8")
        meta, body = parse_frontmatter(content)

        # Get existing note titles for context
        existing = self.vault.db.execute(
            "SELECT id, title FROM notes WHERE type = 'note' ORDER BY title"
        ).fetchall()
        existing_titles = [f"- {r['title']} (id: {r['id']})" for r in existing]

        # Get existing tags
        tags = self.vault.db.execute(
            "SELECT DISTINCT tag FROM tags ORDER BY tag"
        ).fetchall()
        tag_list = [r["tag"] for r in tags]

        # Build prompt
        system, user = get_compile_prompt(
            strategy=strategy,
            raw_title=meta.title,
            raw_body=body,
            existing_notes=existing_titles,
            existing_tags=tag_list,
        )

        # Call LLM
        response = self.provider.complete(
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ]
        )

        # Parse LLM output — expect markdown with frontmatter
        output_content = response.content.strip()

        # Try to extract markdown from code fences
        if "```markdown" in output_content:
            start = output_content.index("```markdown") + len("```markdown")
            end = output_content.index("```", start)
            output_content = output_content[start:end].strip()
        elif "```md" in output_content:
            start = output_content.index("```md") + len("```md")
            end = output_content.index("```", start)
            output_content = output_content[start:end].strip()

        compiled_meta, compiled_body = parse_frontmatter(output_content)

        # Ensure compiled note has correct metadata
        compiled_meta.type = "note"
        compiled_meta.status = "draft"
        compiled_meta.llm_compiled = True
        compiled_meta.llm_model = response.model
        compiled_meta.compile_source = raw["id"]

        # Write the compiled note
        path = write_note(
            self.vault.notes_dir,
            compiled_meta.title,
            body=compiled_body,
            tags=compiled_meta.tags,
            status="draft",
            note_type="note",
            parent=compiled_meta.parent,
            source=meta.source,
            summary=compiled_meta.summary,
        )

        # Update ingest log
        self.vault.db.execute(
            "UPDATE ingest_log SET status = 'compiled', compiled_at = ? WHERE raw_path = ?",
            (datetime.now(timezone.utc).isoformat(), raw["path"]),
        )
        self.vault.db.commit()

        rel = path.relative_to(self.vault.root).as_posix()
        return {
            "id": compiled_meta.id or compiled_meta.title,
            "title": compiled_meta.title,
            "path": rel,
            "source_raw": raw["id"],
        }
