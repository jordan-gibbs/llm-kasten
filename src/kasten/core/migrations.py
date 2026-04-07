"""Schema migration system for kasten SQLite databases."""

from __future__ import annotations

import sqlite3

# Each migration is a SQL script that upgrades from version N-1 to N.
# Migrations MUST be idempotent (safe to re-run).
MIGRATIONS: dict[int, str] = {
    # v1 → v2: no-op, v1 is the initial schema with all current fields
    # Future migrations go here:
    # 3: "ALTER TABLE notes ADD COLUMN new_field TEXT;",
}


def get_schema_version(conn: sqlite3.Connection) -> int:
    try:
        row = conn.execute("SELECT value FROM _meta WHERE key = 'schema_version'").fetchone()
        return int(row[0] if isinstance(row, tuple) else row["value"]) if row else 0
    except sqlite3.OperationalError:
        return 0


def migrate(conn: sqlite3.Connection, target_version: int) -> list[int]:
    """Run pending migrations. Returns list of versions applied."""
    current = get_schema_version(conn)
    if current >= target_version:
        return []

    applied = []
    for version in range(current + 1, target_version + 1):
        sql = MIGRATIONS.get(version)
        if sql:
            conn.executescript(sql)
        conn.execute(
            "INSERT OR REPLACE INTO _meta (key, value) VALUES ('schema_version', ?)",
            (str(version),),
        )
        applied.append(version)

    if applied:
        conn.commit()
    return applied
