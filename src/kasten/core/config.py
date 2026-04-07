"""Vault configuration management (.kasten/config.toml)."""

from __future__ import annotations

import tomllib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class VaultConfig:
    name: str = "Knowledge Base"
    default_status: str = "draft"
    knowledge_dir: str = "knowledge"  # Single visible directory at repo root

    # LLM settings
    llm_provider: str = "openai"
    llm_model: str = "gpt-4o"
    llm_embedding_model: str = "text-embedding-3-small"
    llm_temperature: float = 0.3
    llm_max_tokens: int = 4096

    # Provider-specific API key env vars
    openai_api_key_env: str = "OPENAI_API_KEY"
    anthropic_api_key_env: str = "ANTHROPIC_API_KEY"
    ollama_base_url: str = "http://localhost:11434"

    # Search ranking
    search_title_weight: float = 10.0
    search_body_weight: float = 1.0
    search_tags_weight: float = 5.0
    search_aliases_weight: float = 3.0
    search_boost_evergreen: float = 1.5
    search_penalize_deprecated: float = 0.3
    search_penalize_stale: float = 0.7

    # Sync
    auto_sync: bool = True
    exclude_patterns: list[str] = field(
        default_factory=lambda: [
            ".kasten/*", "exports/*", ".git/*", ".venv/*", "node_modules/*", "templates/*",
            "CLAUDE.md", "AGENTS.md", "agents.md", "GEMINI.md", "README.md", "CHANGELOG.md",
        ]
    )

    # Index
    auto_build_index: bool = True
    index_pages: list[str] = field(
        default_factory=lambda: ["_index", "_tags", "_recent", "_orphans", "_stats"]
    )

    # Raw data
    raw: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def load(cls, config_path: Path) -> VaultConfig:
        if not config_path.exists():
            return cls()
        with open(config_path, "rb") as f:
            data = tomllib.load(f)

        vault = data.get("vault", {})
        llm = data.get("llm", {})
        sync = data.get("sync", {})
        index = data.get("index", {})
        search = data.get("search", {})

        return cls(
            name=vault.get("name", cls.name),
            default_status=vault.get("default_status", cls.default_status),
            knowledge_dir=vault.get("knowledge_dir", cls.knowledge_dir),
            llm_provider=llm.get("provider", cls.llm_provider),
            llm_model=llm.get("model", cls.llm_model),
            llm_embedding_model=llm.get("embedding_model", cls.llm_embedding_model),
            llm_temperature=llm.get("temperature", cls.llm_temperature),
            llm_max_tokens=llm.get("max_tokens", cls.llm_max_tokens),
            openai_api_key_env=llm.get("openai", {}).get(
                "api_key_env", cls.openai_api_key_env
            ),
            anthropic_api_key_env=llm.get("anthropic", {}).get(
                "api_key_env", cls.anthropic_api_key_env
            ),
            ollama_base_url=llm.get("ollama", {}).get("base_url", cls.ollama_base_url),
            search_title_weight=search.get("title_weight", cls.search_title_weight),
            search_body_weight=search.get("body_weight", cls.search_body_weight),
            search_tags_weight=search.get("tags_weight", cls.search_tags_weight),
            search_aliases_weight=search.get("aliases_weight", cls.search_aliases_weight),
            search_boost_evergreen=search.get("boost_evergreen", cls.search_boost_evergreen),
            search_penalize_deprecated=search.get("penalize_deprecated", cls.search_penalize_deprecated),
            search_penalize_stale=search.get("penalize_stale", cls.search_penalize_stale),
            auto_sync=sync.get("auto_sync", cls.auto_sync),
            exclude_patterns=sync.get("exclude_patterns", cls().exclude_patterns),
            auto_build_index=index.get("auto_build", cls.auto_build_index),
            index_pages=index.get("pages", cls().index_pages),
            raw=data,
        )

    @staticmethod
    def _toml_array(items: list[str]) -> str:
        """Format a list as a valid TOML array with double-quoted strings."""
        quoted = ", ".join(f'"{item}"' for item in items)
        return f"[{quoted}]"

    def save(self, config_path: Path) -> None:
        lines = [
            "[vault]",
            f'name = "{self.name}"',
            f'default_status = "{self.default_status}"',
            f'knowledge_dir = "{self.knowledge_dir}"',
            "",
            "[llm]",
            f'provider = "{self.llm_provider}"',
            f'model = "{self.llm_model}"',
            f'embedding_model = "{self.llm_embedding_model}"',
            f"temperature = {self.llm_temperature}",
            f"max_tokens = {self.llm_max_tokens}",
            "",
            "[llm.openai]",
            f'api_key_env = "{self.openai_api_key_env}"',
            "",
            "[llm.anthropic]",
            f'api_key_env = "{self.anthropic_api_key_env}"',
            "",
            "[llm.ollama]",
            f'base_url = "{self.ollama_base_url}"',
            "",
            "[sync]",
            f"auto_sync = {'true' if self.auto_sync else 'false'}",
            f"exclude_patterns = {self._toml_array(self.exclude_patterns)}",
            "",
            "[index]",
            f"auto_build = {'true' if self.auto_build_index else 'false'}",
            f"pages = {self._toml_array(self.index_pages)}",
        ]
        config_path.parent.mkdir(parents=True, exist_ok=True)
        config_path.write_text("\n".join(lines) + "\n")
