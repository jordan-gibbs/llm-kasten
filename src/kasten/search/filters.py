"""Structured field filter builder for search queries."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class SearchFilters:
    tags: list[str] | None = None
    status: str | None = None
    note_type: str | None = None
    after: str | None = None
    before: str | None = None
    path_glob: str | None = None
    parent: str | None = None
    min_words: int | None = None
    max_words: int | None = None

    def to_sql(self, table_alias: str = "n") -> tuple[str, list]:
        """Build SQL WHERE clauses and parameters."""
        clauses: list[str] = []
        params: list = []

        if self.tags:
            for tag in self.tags:
                clauses.append(
                    f"{table_alias}.id IN (SELECT note_id FROM tags WHERE tag = ?)"
                )
                params.append(tag.lower())

        if self.status:
            clauses.append(f"{table_alias}.status = ?")
            params.append(self.status)

        if self.note_type:
            clauses.append(f"{table_alias}.type = ?")
            params.append(self.note_type)

        if self.after:
            clauses.append(f"{table_alias}.created >= ?")
            params.append(self.after)

        if self.before:
            clauses.append(f"{table_alias}.created <= ?")
            params.append(self.before)

        if self.path_glob:
            clauses.append(f"{table_alias}.path GLOB ?")
            params.append(self.path_glob)

        if self.parent:
            clauses.append(f"{table_alias}.parent = ?")
            params.append(self.parent)

        if self.min_words is not None:
            clauses.append(f"{table_alias}.word_count >= ?")
            params.append(self.min_words)

        if self.max_words is not None:
            clauses.append(f"{table_alias}.word_count <= ?")
            params.append(self.max_words)

        where = " AND ".join(clauses) if clauses else "1=1"
        return where, params
