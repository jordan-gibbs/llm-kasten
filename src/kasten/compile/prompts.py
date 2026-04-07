"""Prompt templates for LLM compilation."""

from __future__ import annotations

STRATEGIES = {
    "summarize": (
        "You are a knowledge base compiler. Your job is to take raw source material "
        "and produce a well-structured wiki-style note that summarizes the key information.\n\n"
        "Output a single markdown file with YAML frontmatter including: title, id (slug), "
        "tags (reuse existing tags when possible), summary (one line), and parent (topic category).\n\n"
        "Use [[wiki-links]] to reference other existing notes where relevant.\n"
        "Be comprehensive but concise. Preserve important details, data, and citations."
    ),
    "extract": (
        "You are a knowledge base compiler. Extract the key concepts from this raw material "
        "into separate atomic notes. Each concept should be its own self-contained note.\n\n"
        "For this task, output ONE note that covers the most important concept. "
        "Include [[wiki-links]] to suggest where other concept notes could be created.\n\n"
        "Output markdown with YAML frontmatter: title, id, tags, summary, parent."
    ),
    "restructure": (
        "You are a knowledge base compiler. Take this raw material and restructure it "
        "into a well-organized wiki entry with clear sections, definitions, examples, "
        "and cross-references.\n\n"
        "Output markdown with YAML frontmatter: title, id, tags, summary, parent.\n"
        "Use [[wiki-links]] to connect to existing notes."
    ),
}


def get_compile_prompt(
    strategy: str,
    raw_title: str,
    raw_body: str,
    existing_notes: list[str],
    existing_tags: list[str],
) -> tuple[str, str]:
    """Build system and user prompts for compilation."""
    system = STRATEGIES.get(strategy, STRATEGIES["summarize"])

    notes_ctx = "\n".join(existing_notes[:50]) if existing_notes else "(none yet)"
    tags_ctx = ", ".join(existing_tags[:100]) if existing_tags else "(none yet)"

    user = (
        f"## Existing notes in the knowledge base:\n{notes_ctx}\n\n"
        f"## Existing tags: {tags_ctx}\n\n"
        f"## Raw material to compile:\n\n"
        f"### {raw_title}\n\n{raw_body}"
    )

    return system, user
