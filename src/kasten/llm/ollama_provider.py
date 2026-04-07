"""Ollama local LLM provider."""

from __future__ import annotations

import struct

from kasten.llm.provider import LLMProvider, LLMResponse


class OllamaProvider(LLMProvider):
    def __init__(self, config: dict) -> None:
        import httpx

        self.base_url = config.get("ollama", {}).get("base_url", "http://localhost:11434")
        self.model = config.get("model", "llama3.1")
        self.client = httpx.Client(base_url=self.base_url, timeout=120)

    def complete(self, messages, temperature=0.3, max_tokens=4096) -> LLMResponse:
        resp = self.client.post(
            "/api/chat",
            json={
                "model": self.model,
                "messages": messages,
                "stream": False,
                "options": {"temperature": temperature, "num_predict": max_tokens},
            },
        )
        resp.raise_for_status()
        data = resp.json()
        return LLMResponse(
            content=data.get("message", {}).get("content", ""),
            model=self.model,
            usage={
                "prompt_tokens": data.get("prompt_eval_count", 0),
                "completion_tokens": data.get("eval_count", 0),
            },
        )

    def embed(self, text: str) -> bytes:
        resp = self.client.post(
            "/api/embeddings",
            json={"model": self.model, "prompt": text},
        )
        resp.raise_for_status()
        vec = resp.json().get("embedding", [])
        return struct.pack(f"{len(vec)}f", *vec)

    def embed_batch(self, texts: list[str]) -> list[bytes]:
        return [self.embed(t) for t in texts]

    @property
    def name(self) -> str:
        return f"ollama:{self.model}"

    @property
    def supports_embeddings(self) -> bool:
        return True
