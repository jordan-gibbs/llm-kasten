"""OpenAI-compatible LLM provider."""

from __future__ import annotations

import os
import struct

from kasten.llm.provider import LLMProvider, LLMResponse


class OpenAIProvider(LLMProvider):
    def __init__(self, config: dict) -> None:
        import openai

        api_key_env = config.get("openai", {}).get("api_key_env", "OPENAI_API_KEY")
        api_key = os.environ.get(api_key_env, "")
        base_url = config.get("openai", {}).get("base_url") or None
        self.client = openai.OpenAI(api_key=api_key, base_url=base_url)
        self.model = config.get("model", "gpt-4o")
        self.embedding_model = config.get("embedding_model", "text-embedding-3-small")

    def complete(self, messages, temperature=0.3, max_tokens=4096) -> LLMResponse:
        resp = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        choice = resp.choices[0]
        return LLMResponse(
            content=choice.message.content or "",
            model=resp.model,
            usage={
                "prompt_tokens": resp.usage.prompt_tokens if resp.usage else 0,
                "completion_tokens": resp.usage.completion_tokens if resp.usage else 0,
            },
        )

    def embed(self, text: str) -> bytes:
        resp = self.client.embeddings.create(model=self.embedding_model, input=text)
        vec = resp.data[0].embedding
        return struct.pack(f"{len(vec)}f", *vec)

    def embed_batch(self, texts: list[str]) -> list[bytes]:
        resp = self.client.embeddings.create(model=self.embedding_model, input=texts)
        results = []
        for item in sorted(resp.data, key=lambda x: x.index):
            vec = item.embedding
            results.append(struct.pack(f"{len(vec)}f", *vec))
        return results

    @property
    def name(self) -> str:
        return f"openai:{self.model}"

    @property
    def supports_embeddings(self) -> bool:
        return True
