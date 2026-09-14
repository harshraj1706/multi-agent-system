import os
from functools import lru_cache
from typing import Any

from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain_core.messages import AIMessage
from langchain_core.messages import BaseMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import Runnable
import random
import time
import requests

from tool import scrape_url, web_search

load_dotenv()


def _require_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"{name} is not set. Add it to your .env file.")
    return value


@lru_cache(maxsize=1)
def _get_llm() -> Runnable:
    """Build the Gemini chat model only when a pipeline call needs it."""
    provider = os.getenv("LLM_PROVIDER", "gemini").lower()
    if provider != "gemini":
        raise RuntimeError(
            "Only Gemini is configured. Set LLM_PROVIDER=gemini in your .env file."
        )

    return GeminiChatModel(
        model=os.getenv("LLM_MODEL", "gemini-3.8-flash"),
        fallback_model=os.getenv("LLM_FALLBACK_MODEL", "gemini-3.6-flash"),
        api_key=_require_env("GEMINI_API_KEY"),
        temperature=float(os.getenv("LLM_TEMPERATURE", "0.2")),
        max_output_tokens=int(os.getenv("LLM_MAX_TOKENS", "4000")),
    )


class GeminiChatModel(Runnable):
    """Minimal Gemini REST adapter with retry, backoff, and model fallback for LangChain."""

    def __init__(
        self,
        model: str,
        api_key: str,
        fallback_model: str | None = None,
        temperature: float = 0.2,
        max_output_tokens: int = 4000,
        max_retries: int = 3,
        initial_backoff: float = 2.0,
    ):
        self.model = model
        self.fallback_model = fallback_model
        self.api_key = api_key
        self.temperature = temperature
        self.max_output_tokens = max_output_tokens
        self.max_retries = max_retries
        self.initial_backoff = initial_backoff

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
        if self.fallback_model and self.fallback_model != self.model:
            candidate_models.append(self.fallback_model)

        last_error = None

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
                        timeout=120,
                    )
                except (requests.RequestException, TimeoutError) as net_err:
                    last_error = net_err
                    if attempt < self.max_retries - 1:
                        sleep_time = self.initial_backoff * (2 ** attempt) + random.uniform(0.5, 1.5)
                        print(f"[Gemini] Network error with {model_name}: {net_err}. Retrying in {sleep_time:.1f}s...")
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

                    return AIMessage(content=output)

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
                    sleep_time = self.initial_backoff * (2 ** attempt) + random.uniform(0.5, 1.5)
                    print(
                        f"[Gemini] {model_name} returned {status_code} ({detail}). "
                        f"Retrying in {sleep_time:.1f}s (attempt {attempt + 1}/{self.max_retries})..."
                    )
                    time.sleep(sleep_time)
                    continue

                if is_transient and model_idx < len(candidate_models) - 1:
                    print(
                        f"[Gemini] {model_name} unavailable after {attempt + 1} attempts ({detail}). "
                        f"Falling back to {candidate_models[model_idx + 1]}..."
                    )
                    break

                raise last_error

        raise last_error or RuntimeError("Gemini API call failed with all candidate models.")


class LazyChain:
    """Small wrapper that preserves `.invoke()` while delaying API setup."""

    def __init__(self, prompt: ChatPromptTemplate):
        self.prompt = prompt

    @lru_cache(maxsize=1)
    def _chain(self):
        return self.prompt | _get_llm() | StrOutputParser()

    def invoke(self, inputs: dict) -> str:
        return self._chain().invoke(inputs)


def _message_text(message: BaseMessage | object) -> str:
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


class AgentRunner:
    """Compatibility wrapper for LangChain 1.x agent graphs."""

    def __init__(self, agent_graph, recursion_limit: int = 10):
        self.agent_graph = agent_graph
        self.recursion_limit = recursion_limit

    def invoke(self, inputs: dict) -> dict:
        user_input = inputs.get("input")
        if not user_input:
            raise ValueError("AgentRunner.invoke expects an 'input' value.")

        result = self.agent_graph.invoke(
            {"messages": [{"role": "user", "content": user_input}]},
            config={"recursion_limit": self.recursion_limit},
        )
        messages = result.get("messages", [])
        output = _message_text(messages[-1]) if messages else ""
        return {"output": output, "messages": messages}


class DirectSearchRunner:
    """Run the search tool once without a LangGraph agent loop."""

    def __init__(self, search_tool):
        self.search_tool = search_tool

    def invoke(self, inputs: dict) -> dict:
        user_input = inputs.get("input")
        if not user_input:
            raise ValueError("DirectSearchRunner.invoke expects an 'input' value.")

        output = self.search_tool.invoke({"query": user_input})
        return {"output": str(output), "messages": []}


search_system_prompt = """
You are an expert Research Agent.

Your task is to search for comprehensive, reliable, and detailed
information about the given topic.

Use the web_search tool to find recent and relevant results.
Call the web_search tool once, then summarize the best evidence.
"""


def search_agent():
    return DirectSearchRunner(web_search)


reader_system_prompt = """
You are an expert Web Content Extraction Agent.

Your task is to extract and analyze content from relevant URLs
found in the provided search results.

Use the scrape_url tool to fetch full article text from specific URLs.
Focus on the most informative and on-topic pages.
Scrape no more than two URLs.
Summarize the key information you extract.
"""


def reader_agent():
    agent = create_agent(
        model=_get_llm(),
        tools=[scrape_url],
        system_prompt=reader_system_prompt,
    )
    return AgentRunner(agent, recursion_limit=6)


writer_prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            """
You are an expert Research Analyst and Technical Writer.

Your task is to generate a comprehensive, accurate, and well-structured research report.

You will be given:

1. A research topic.
2. Combined research data containing:
   - Search results collected from Tavily.
   - Detailed website content extracted using Readability and BeautifulSoup.

Instructions:

- Analyze all provided information carefully.
- Synthesize information from multiple sources.
- Remove duplicate information.
- Cross-check facts whenever possible.
- Write in a clear, professional, and objective style.
- Do not copy source text verbatim.
- Explain concepts thoroughly.
- Include important insights, trends, challenges, benefits,
  limitations, and future developments.
- Ignore irrelevant content such as advertisements, navigation menus,
  cookie notices, and website boilerplate text.
- If sources contain conflicting information, prefer the most
  consistent and well-supported evidence.

Structure the report using the following format:

# Title

## Executive Summary

## Introduction

## Key Concepts

## Detailed Analysis

## Current Developments

## Advantages

## Limitations and Challenges

## Future Outlook

## Conclusion

The report should be focused, informative, and suitable for
professional research purposes.
""",
        ),
        (
            "human",
            """
Research Topic:
{topic}

Research Data:
{research_combined}

Generate a complete research report.
""",
        ),
    ]
)

writer_chain = LazyChain(writer_prompt)


review_prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            """
You are an expert Research Reviewer and Quality Assurance Analyst.

Your task is to critically evaluate a research report.

Evaluate the report on the following criteria:

1. Accuracy
   - Are the facts logically consistent?
   - Are claims properly supported?

2. Completeness
   - Does the report sufficiently cover the topic?
   - Are important aspects missing?

3. Structure and Organization
   - Is the report logically organized?
   - Are sections clear and coherent?

4. Clarity and Readability
   - Is the writing easy to understand?
   - Are explanations clear?

5. Depth of Analysis
   - Does the report provide meaningful insights?
   - Does it go beyond superficial explanations?

6. Objectivity
   - Is the report unbiased and balanced?

7. Source Utilization
   - Does the report appear to effectively synthesize
     information from multiple sources?

Provide:

# Overall Score
Rate the report from 1 to 10.

# Strengths
List the strongest aspects of the report.

# Weaknesses
List the major weaknesses.

# Missing Information
Identify important missing topics or gaps.

# Improvement Suggestions
Provide specific recommendations for improvement.

# Final Verdict
Briefly summarize the overall quality of the report.

Be constructive, detailed, and objective.
""",
        ),
        (
            "human",
            """
Research Topic:
{topic}

Generated Report:
{report}

Evaluate this report and provide a detailed review.
""",
        ),
    ]
)

review_chain = LazyChain(review_prompt)
