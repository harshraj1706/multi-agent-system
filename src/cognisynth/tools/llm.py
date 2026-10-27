"""
Gemini Chat Model adapter with exponential backoff, jitter, and fallback resilience.
Preserves existing working resilience logic while providing structured telemetry.
"""

import os
import random
import time
from functools import lru_cache
from typing import Any, Optional
import requests
from langchain_core.messages import AIMessage, BaseMessage
from langchain_core.runnables import Runnable

from cognisynth.config import settings
from cognisynth.logging_config import logger


def _message_text(message: BaseMessage | object) -> str:
    """Extract clean string text from any LangChain message or dict representation."""
    content = getattr(message, "content", message)
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for item in content:
            if isinstance(item, dict):
                parts.append(str(item.get("text") or item.get("content") or item))
            else:
                parts.append(str(item))
        return "\n".join(parts)
    return str(content)


class GeminiChatModel(Runnable):
    """
    Resilient Google Gemini REST adapter with automatic exponential backoff,
    jitter, and graceful fallback to a secondary model on capacity spikes (429/503).
    """

    def __init__(
        self,
        model: Optional[str] = None,
        api_key: Optional[str] = None,
        fallback_model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_output_tokens: Optional[int] = None,
        max_retries: Optional[int] = None,
        initial_backoff: Optional[float] = None,
    ):
        self.model = model or settings.llm_model
        self.fallback_model = fallback_model or settings.llm_fallback_model
        self.api_key = api_key or settings.gemini_api_key
        self.temperature = temperature if temperature is not None else settings.llm_temperature
        self.max_output_tokens = max_output_tokens or settings.llm_max_tokens
        self.max_retries = max_retries or settings.llm_max_retries
        self.initial_backoff = initial_backoff or settings.llm_initial_backoff

        # Telemetry stats
        self.total_prompt_tokens = 0
        self.total_completion_tokens = 0
        self.call_count = 0
        self.retry_count = 0
        self.fallback_count = 0

    def _messages_from_input(self, input_value: Any) -> list[BaseMessage | object]:
        if hasattr(input_value, "to_messages"):
            return list(input_value.to_messages())
        if isinstance(input_value, list):
            return input_value
        return [input_value]

    def invoke(self, input: Any, config: dict | None = None, **kwargs: Any) -> AIMessage:
        system_parts = []
        contents = []

        for message in self._messages_from_input(input):
            text = _message_text(message)
            if not text:
                continue

            message_type = getattr(message, "type", "")
            if message_type == "system":
                system_parts.append(text)
                continue

            role = "model" if message_type == "ai" else "user"
            contents.append({"role": role, "parts": [{"text": text}]})

        if not contents:
            contents.append({"role": "user", "parts": [{"text": ""}]})

        payload = {
            "contents": contents,
            "generationConfig": {
                "temperature": self.temperature,
                "maxOutputTokens": self.max_output_tokens,
            },
        }
        if system_parts:
            payload["systemInstruction"] = {
                "parts": [{"text": "\n\n".join(system_parts)}]
            }

        candidate_models = [self.model]
        if self.fallback_model and self.fallback_model not in candidate_models:
            candidate_models.append(self.fallback_model)
        for alt in ["gemini-3.6-flash", "gemini-3.7-flash", "gemini-3.8-flash"]:
            if alt not in candidate_models:
                candidate_models.append(alt)

        last_error = None
        self.call_count += 1

        for model_idx, model_name in enumerate(candidate_models):
            url = (
                "https://generativelanguage.googleapis.com/v1beta/"
                f"models/{model_name}:generateContent"
            )

            for attempt in range(self.max_retries):
                try:
                    response = requests.post(
                        url,
                        params={"key": self.api_key},
                        json=payload,
                        timeout=settings.request_timeout,
                    )
                except (requests.RequestException, TimeoutError) as net_err:
                    last_error = net_err
                    self.retry_count += 1
                    if attempt < self.max_retries - 1:
                        sleep_time = self.initial_backoff * (2 ** attempt) + random.uniform(0.5, 1.5)
                        logger.warning(
                            f"[Gemini] Network error with {model_name}: {net_err}. "
                            f"Retrying in {sleep_time:.1f}s (attempt {attempt + 1}/{self.max_retries})..."
                        )
                        time.sleep(sleep_time)
                        continue
                    break

                if response.status_code == 200:
                    data = response.json()
                    text_parts = []
                    for candidate in data.get("candidates", []):
                        for part in candidate.get("content", {}).get("parts", []):
                            if "text" in part:
                                text_parts.append(part["text"])

                    output = "\n".join(text_parts).strip()
                    if not output:
                        raise RuntimeError(f"Gemini API returned no text: {data}")

                    # Estimate or record tokens
                    usage = data.get("usageMetadata", {})
                    p_tok = usage.get("promptTokenCount", len(str(contents)) // 4)
                    c_tok = usage.get("candidatesTokenCount", len(output) // 4)
                    self.total_prompt_tokens += p_tok
                    self.total_completion_tokens += c_tok

                    return AIMessage(
                        content=output,
                        response_metadata={
                            "model": model_name,
                            "prompt_tokens": p_tok,
                            "completion_tokens": c_tok,
                            "total_tokens": p_tok + c_tok,
                        },
                    )

                detail = response.text[:500]
                try:
                    detail = response.json().get("error", {}).get("message", detail)
                except ValueError:
                    pass

                last_error = RuntimeError(f"Gemini API request failed ({model_name}): {detail}")
                status_code = response.status_code
                is_transient = (
                    status_code in (429, 500, 502, 503, 504)
                    or "high demand" in detail.lower()
                    or "resource has been exhausted" in detail.lower()
                    or "quota" in detail.lower()
                )

                if is_transient and attempt < self.max_retries - 1:
                    self.retry_count += 1
                    sleep_time = self.initial_backoff * (2 ** attempt) + random.uniform(0.5, 1.5)
                    logger.warning(
                        f"[Gemini] {model_name} returned {status_code} ({detail}). "
                        f"Retrying in {sleep_time:.1f}s (attempt {attempt + 1}/{self.max_retries})..."
                    )
                    time.sleep(sleep_time)
                    continue

                if is_transient and model_idx < len(candidate_models) - 1:
                    self.fallback_count += 1
                    logger.warning(
                        f"[Gemini] {model_name} unavailable after {attempt + 1} attempts ({detail}). "
                        f"Falling back to {candidate_models[model_idx + 1]}..."
                    )
                    break

                raise last_error

        raise last_error or RuntimeError("Gemini API call failed with all candidate models.")


@lru_cache(maxsize=1)
def get_default_llm() -> GeminiChatModel:
    """Singleton getter for the configured Gemini LLM adapter."""
    return GeminiChatModel()
