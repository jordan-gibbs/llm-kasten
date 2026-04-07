"""Abstract LLM provider interface and factory."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class LLMResponse:
    content: str
    model: str
    usage: dict


class LLMProvider(ABC):
    """Abstract interface for LLM providers."""

    @abstractmethod
    def complete(
        self,
        messages: list[dict[str, str]],
        temperature: float = 0.3,
        max_tokens: int = 4096,
    ) -> LLMResponse:
        ...

    @abstractmethod
    def embed(self, text: str) -> bytes:
        """Return float32 vector as packed bytes."""
        ...

    @abstractmethod
    def embed_batch(self, texts: list[str]) -> list[bytes]:
        ...

    @property
    @abstractmethod
    def name(self) -> str:
        ...

    @property
    @abstractmethod
    def supports_embeddings(self) -> bool:
        ...


def get_provider(config: dict) -> LLMProvider:
    """Factory: instantiate provider from config dict."""
    llm_config = config.get("llm", {})
    provider_name = llm_config.get("provider", "openai")

    match provider_name:
        case "openai":
            from kasten.llm.openai_provider import OpenAIProvider
            return OpenAIProvider(llm_config)
        case "anthropic":
            from kasten.llm.anthropic_provider import AnthropicProvider
            return AnthropicProvider(llm_config)
        case "ollama":
            from kasten.llm.ollama_provider import OllamaProvider
            return OllamaProvider(llm_config)
        case _:
            raise ValueError(f"Unknown LLM provider: {provider_name}")
