"""Vault discovery, initialization, and management."""

from __future__ import annotations

import sqlite3
from pathlib import Path

from kasten.core.config import VaultConfig
from kasten.core.db import get_connection, init_schema

KASTEN_DIR = ".kasten"
CONFIG_FILE = "config.toml"
DB_FILE = "kasten.db"


class VaultError(Exception):
    pass


class Vault:
    """Represents a kasten knowledge base vault."""

    def __init__(self, root: Path) -> None:
        self.root = root.resolve()
        self.kasten_dir = self.root / KASTEN_DIR
        self.config_path = self.kasten_dir / CONFIG_FILE
        self.db_path = self.kasten_dir / DB_FILE
        self._conn: sqlite3.Connection | None = None
        self._config: VaultConfig | None = None

    @property
    def config(self) -> VaultConfig:
        if self._config is None:
            self._config = VaultConfig.load(self.config_path)
        return self._config

    @property
    def db(self) -> sqlite3.Connection:
        if self._conn is None:
            self._conn = get_connection(self.db_path)
        return self._conn

    @property
    def is_initialized(self) -> bool:
        return self.kasten_dir.is_dir() and self.db_path.exists()

    # --- Path properties: single source of truth for directory layout ---

    @property
    def knowledge_dir(self) -> Path:
        """The one visible directory at repo root (default: knowledge/)."""
        return self.root / self.config.knowledge_dir

    @property
    def notes_dir(self) -> Path:
        return self.knowledge_dir / "notes"

    @property
    def index_dir(self) -> Path:
        return self.knowledge_dir / "index"

    @property
    def templates_dir(self) -> Path:
        """Templates live inside .kasten/ (hidden)."""
        return self.kasten_dir / "templates"

    @property
    def exports_dir(self) -> Path:
        """Exports live inside .kasten/ (hidden)."""
        return self.kasten_dir / "exports"

    def close(self) -> None:
        if self._conn is not None:
            self._conn.close()
            self._conn = None

    def __enter__(self) -> Vault:
        return self

    def __exit__(self, *args) -> None:
        self.close()

    @staticmethod
    def init(root: Path, name: str = "Knowledge Base", knowledge_dir: str = "knowledge", agents: list[str] | None = None) -> Vault:
        """Initialize a new vault at the given path."""
        root = root.resolve()
        kasten_dir = root / KASTEN_DIR

        if kasten_dir.exists():
            raise VaultError(f"Vault already initialized at {root}")

        # Create .kasten/ structure (hidden)
        kasten_dir.mkdir(parents=True)
        (kasten_dir / "templates").mkdir()
        (kasten_dir / "exports").mkdir()

        # Create the one visible directory
        kb_dir = root / knowledge_dir
        (kb_dir / "notes").mkdir(parents=True, exist_ok=True)
        (kb_dir / "index").mkdir(exist_ok=True)

        # Write config
        config = VaultConfig(name=name, knowledge_dir=knowledge_dir)
        config.save(kasten_dir / CONFIG_FILE)

        # Initialize database
        vault = Vault(root)
        init_schema(vault.db)

        # Write default note template
        template_path = kasten_dir / "templates" / "note.md"
        template_path.write_text(
            "---\n"
            "title: \"{{ title }}\"\n"
            "id: \"{{ id }}\"\n"
            "tags: []\n"
            "status: draft\n"
            "type: note\n"
            "created: {{ created }}\n"
            "---\n\n"
            "# {{ title }}\n\n"
        )

        # Inject kasten docs into agent config files (CLAUDE.md, AGENTS.md)
        from kasten.core.agent_docs import inject_agent_docs
        inject_agent_docs(root, agents=agents)

        return vault

    @staticmethod
    def discover(start: Path | None = None) -> Vault:
        """Walk up from start (default: cwd) to find a vault root."""
        current = (start or Path.cwd()).resolve()
        while True:
            if (current / KASTEN_DIR).is_dir():
                return Vault(current)
            parent = current.parent
            if parent == current:
                break
            current = parent
        raise VaultError(
            "No kasten vault found. Run 'kasten init' to create one."
        )

    def auto_sync(self) -> None:
        """Run an incremental sync if auto_sync is enabled."""
        if not self.config.auto_sync:
            return
        from kasten.core.sync import execute_sync, compute_sync_plan

        plan = compute_sync_plan(self)
        if plan.to_add or plan.to_update or plan.to_delete:
            execute_sync(self, plan)
