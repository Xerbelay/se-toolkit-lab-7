from __future__ import annotations

import json
from dataclasses import dataclass

import httpx

from config import get_settings


class LLMError(Exception):
    pass


@dataclass
class LLMClient:
    base_url: str
    api_key: str
    model: str
    timeout: float = 60.0

    @property
    def headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    def chat(self, messages: list[dict], tools: list[dict] | None = None) -> dict:
        url = f"{self.base_url.rstrip('/')}/chat/completions"

        payload: dict = {
            "model": self.model,
            "messages": messages,
            "temperature": 0.2,
        }

        if tools:
            payload["tools"] = tools
            payload["tool_choice"] = "auto"

        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.post(url, headers=self.headers, json=payload)
                if response.status_code >= 400:
                    raise LLMError(
                        f"LLM error: HTTP {response.status_code} {response.reason_phrase}"
                    )
                return response.json()
        except httpx.RequestError as exc:
            raise LLMError(f"LLM error: {exc}") from exc


def get_llm_client() -> LLMClient:
    settings = get_settings()

    if not settings.llm_api_key:
        raise LLMError("LLM error: LLM_API_KEY is missing in .env.bot.secret")

    return LLMClient(
        base_url=settings.llm_api_base_url,
        api_key=settings.llm_api_key,
        model=settings.llm_api_model,
    )
