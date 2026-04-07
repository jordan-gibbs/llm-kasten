"""Embedding provider abstraction."""

from __future__ import annotations

from kasten.llm.provider import LLMProvider


def embed_note(provider: LLMProvider, title: str, body: str, tags: list[str]) -> bytes:
    """Create an embedding for a note by combining its key fields."""
    text = f"{title}\n\nTags: {', '.join(tags)}\n\n{body[:8000]}"
    return provider.embed(text)
