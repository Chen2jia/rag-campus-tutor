from __future__ import annotations

from dataclasses import dataclass
from importlib import import_module
from typing import Any

from app.core.config import settings


@dataclass(frozen=True)
class EmbeddingResult:
    text: str
    vector: list[float]
    model: str


class EmbeddingError(RuntimeError):
    pass


class EmbeddingService:
    """Small OpenAI embedding wrapper with lazy import and retry support."""

    def __init__(self, model: str | None = None, max_retries: int = 3) -> None:
        self.model = model or settings.embedding_model
        self.max_retries = max_retries

    async def embed_text(self, text: str) -> EmbeddingResult:
        clean_text = self._normalize_text(text)
        if not clean_text:
            raise EmbeddingError("Cannot embed empty text")

        last_error: Exception | None = None
        for attempt in range(1, self.max_retries + 1):
            try:
                vector = await self._request_embedding(clean_text)
                return EmbeddingResult(text=clean_text, vector=vector, model=self.model)
            except Exception as exc:  # pragma: no cover - network/client failures
                last_error = exc
                if attempt == self.max_retries:
                    break
        raise EmbeddingError("Embedding request failed") from last_error

    async def embed_texts(self, texts: list[str]) -> list[EmbeddingResult]:
        results: list[EmbeddingResult] = []
        for text in texts:
            results.append(await self.embed_text(text))
        return results

    async def _request_embedding(self, text: str) -> list[float]:
        client = self._build_client()
        response = await client.embeddings.create(model=self.model, input=text)
        return self._extract_vector(response)

    @staticmethod
    def _normalize_text(text: str) -> str:
        return " ".join(text.split()).strip()

    def _build_client(self) -> Any:
        if not settings.openai_api_key.strip() or settings.openai_api_key.strip() in {"sk-change-me", "change-me"}:
            raise EmbeddingError("OPENAI_API_KEY is not configured")

        openai_module = import_module("openai")
        return openai_module.AsyncOpenAI(api_key=settings.openai_api_key)

    @staticmethod
    def _extract_vector(response: Any) -> list[float]:
        data = getattr(response, "data", None)
        if not data:
            raise EmbeddingError("OpenAI embeddings response is empty")

        vector = getattr(data[0], "embedding", None)
        if not isinstance(vector, list) or not vector:
            raise EmbeddingError("OpenAI embeddings response did not include a vector")

        return [float(value) for value in vector]
