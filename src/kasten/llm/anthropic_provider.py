"""Anthropic Claude LLM provider."""

from __future__ import annotations

import os

from kasten.llm.provider import LLMProvider, LLMResponse


class AnthropicProvider(LLMProvider):
    def __init__(self, config: dict) -> None:
        import anthropic

        api_key_env = config.get("anthropic", {}).get("api_key_env", "ANTHROPIC_API_KEY")
        api_key = os.environ.get(api_key_env, "")
        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = config.get("model", "claude-sonnet-4-20250514")

    def complete(self, messages, temperature=0.3, max_tokens=4096) -> LLMResponse:
        # Extract system message if present
        system = ""
        user_messages = []
        for m in messages:
            if m["role"] == "system":
                system = m["content"]
            else:
                user_messages.append(m)

        kwargs = {
            "model": self.model,
            "messages": user_messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        if system:
            kwargs["system"] = system

        resp = self.client.messages.create(**kwargs)
        content = resp.content[0].text if resp.content else ""
        return LLMResponse(
            content=content,
            model=resp.model,
            usage={
                "prompt_tokens": resp.usage.input_tokens,
                "completion_tokens": resp.usage.output_tokens,
            },
        )

    def embed(self, text: str) -> bytes:
        raise NotImplementedError("Anthropic does not provide embeddings. Use OpenAI or local embeddings.")

    def embed_batch(self, texts: list[str]) -> list[bytes]:
        raise NotImplementedError("Anthropic does not provide embeddings.")

    @property
    def name(self) -> str:
        return f"anthropic:{self.model}"

    @property
    def supports_embeddings(self) -> bool:
        return False
