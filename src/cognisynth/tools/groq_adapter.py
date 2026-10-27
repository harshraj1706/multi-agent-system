"""
Groq REST API Model Adapter.
Executes high-throughput inference across Groq-hosted open-source models:
- openai/gpt-oss-120b (Deep Reasoning)
- qwen/qwen3.6-27b (Fast Tasks & Claim Extraction)
- groq/compound-mini (Research Synthesis & Planning)
"""

import time
from typing import Any, Optional
import requests
from langchain_core.messages import AIMessage, BaseMessage
from langchain_core.runnables import Runnable

from cognisynth.config import settings
from cognisynth.logging_config import logger
from cognisynth.tools.llm import _message_text


class GroqChatModel(Runnable):
    """Resilient REST adapter for Groq API models."""

    def __init__(
        self,
        model: str,
        api_key: Optional[str] = None,
        temperature: float = 0.2,
        max_tokens: int = 4000,
        max_retries: int = 3,
    ):
        self.model = model
        self.api_key = api_key or settings.groq_api_key
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.max_retries = max_retries

    def _messages_from_input(self, input_value: Any) -> list[BaseMessage | object]:
        if hasattr(input_value, "to_messages"):
            return list(input_value.to_messages())
        if isinstance(input_value, list):
            return input_value
        return [input_value]

    def invoke(self, input: Any, config: dict | None = None, **kwargs: Any) -> AIMessage:
        if not self.api_key:
            raise RuntimeError("GROQ_API_KEY is not configured in environment or .env file.")

        messages_payload = []
        for message in self._messages_from_input(input):
            text = _message_text(message)
            if not text:
                continue

            msg_type = getattr(message, "type", "")
            if msg_type == "system":
                role = "system"
            elif msg_type == "ai":
                role = "assistant"
            else:
                role = "user"
            messages_payload.append({"role": role, "content": text})

        if not messages_payload:
            messages_payload.append({"role": "user", "content": "Hello"})

        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.model,
            "messages": messages_payload,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
        }

        last_error = None
        for attempt in range(self.max_retries):
            try:
                response = requests.post(url, headers=headers, json=payload, timeout=settings.request_timeout)
                if response.status_code == 200:
                    data = response.json()
                    choices = data.get("choices", [])
                    if choices:
                        content = choices[0].get("message", {}).get("content", "").strip()
                        usage = data.get("usage", {})
                        return AIMessage(
                            content=content,
                            response_metadata={
                                "model": self.model,
                                "provider": "groq",
                                "prompt_tokens": usage.get("prompt_tokens", 0),
                                "completion_tokens": usage.get("completion_tokens", 0),
                            },
                        )

                detail = response.text[:400]
                last_error = RuntimeError(f"Groq API error ({self.model}, HTTP {response.status_code}): {detail}")
                if response.status_code in (429, 500, 503) and attempt < self.max_retries - 1:
                    time.sleep(1.5 * (attempt + 1))
                    continue
                raise last_error

            except Exception as exc:
                last_error = exc
                if attempt < self.max_retries - 1:
                    time.sleep(1.5 * (attempt + 1))
                    continue
                raise last_error

        raise last_error or RuntimeError(f"Groq invocation failed for {self.model}")
