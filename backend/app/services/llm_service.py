from __future__ import annotations

from dataclasses import dataclass
from importlib import import_module
from typing import Any
from urllib.parse import urlparse

from app.core.config import settings


@dataclass(frozen=True)
class LlmResponse:
    content: str
    provider: str
    model: str


@dataclass(frozen=True)
class LlmConfigStatus:
    configured: bool
    provider: str
    model: str | None
    base_url_host: str | None
    missing: list[str]


class LlmServiceError(RuntimeError):
    pass


class LlmService:
    """OpenAI-compatible chat client, usable with OpenAI or DeepSeek base URLs."""

    async def generate(
        self,
        messages: list[dict[str, str]],
        temperature: float = 0.2,
    ) -> LlmResponse:
        if not self.is_configured():
            raise LlmServiceError("OPENAI_API_KEY and OPENAI_MODEL are not configured")

        openai_module = import_module("openai")
        client_kwargs: dict[str, str] = {"api_key": settings.openai_api_key}
        if settings.openai_base_url.strip():
            client_kwargs["base_url"] = settings.openai_base_url.strip()

        client = openai_module.AsyncOpenAI(**client_kwargs)
        response = await client.chat.completions.create(
            model=settings.openai_model,
            messages=messages,
            temperature=temperature,
        )
        return LlmResponse(
            content=self._extract_message_text(response),
            provider=self._provider_name(),
            model=settings.openai_model,
        )

    @staticmethod
    def is_configured() -> bool:
        api_key = settings.openai_api_key.strip()
        model = settings.openai_model.strip()
        return bool(api_key and model and api_key not in {"sk-change-me", "change-me"})

    @classmethod
    def config_status(cls) -> LlmConfigStatus:
        api_key = settings.openai_api_key.strip()
        model = settings.openai_model.strip()
        missing: list[str] = []
        if not api_key or api_key in {"sk-change-me", "change-me"}:
            missing.append("OPENAI_API_KEY")
        if not model:
            missing.append("OPENAI_MODEL")

        return LlmConfigStatus(
            configured=not missing,
            provider=cls._provider_name(),
            model=model or None,
            base_url_host=cls._base_url_host(),
            missing=missing,
        )

    @staticmethod
    def _extract_message_text(response: Any) -> str:
        content = response.choices[0].message.content
        if isinstance(content, str) and content.strip():
            return content.strip()
        raise LlmServiceError("LLM response did not include valid text")

    @staticmethod
    def _provider_name() -> str:
        base_url = settings.openai_base_url.strip().lower()
        if "deepseek" in base_url:
            return "deepseek"
        return "openai-compatible"

    @staticmethod
    def _base_url_host() -> str | None:
        base_url = settings.openai_base_url.strip()
        if not base_url:
            return None
        parsed = urlparse(base_url)
        host = parsed.netloc or parsed.path.split("/")[0]
        return host or None
