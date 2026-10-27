"""
Token usage and cost aggregation telemetry.
Estimates expenditure based on provider token counters and model price tiers.
"""

from typing import Any


# Approximate pricing per 1 Million tokens (USD)
MODEL_PRICING = {
    "gemini-3.8-flash": {"input_per_million": 0.15, "output_per_million": 0.60},
    "gemini-3.6-flash": {"input_per_million": 0.15, "output_per_million": 0.60},
    "default": {"input_per_million": 0.20, "output_per_million": 0.80},
}


class CostTracker:
    """Aggregates LLM token usage and calculates estimated USD operational cost."""

    def __init__(self):
        self.prompt_tokens = 0
        self.completion_tokens = 0
        self.llm_call_count = 0
        self.search_call_count = 0
        self.scrape_call_count = 0

    def record_llm_call(self, prompt_tokens: int, completion_tokens: int) -> None:
        self.prompt_tokens += prompt_tokens
        self.completion_tokens += completion_tokens
        self.llm_call_count += 1

    def record_search(self, count: int = 1) -> None:
        self.search_call_count += count

    def record_scrape(self, count: int = 1) -> None:
        self.scrape_call_count += count

    def calculate_cost(self, model_name: str = "gemini-3.8-flash") -> float:
        tier = MODEL_PRICING.get(model_name, MODEL_PRICING["default"])
        input_cost = (self.prompt_tokens / 1_000_000.0) * tier["input_per_million"]
        output_cost = (self.completion_tokens / 1_000_000.0) * tier["output_per_million"]
        return round(input_cost + output_cost, 6)

    def to_dict(self, model_name: str = "gemini-3.8-flash") -> dict[str, Any]:
        return {
            "prompt_tokens": self.prompt_tokens,
            "completion_tokens": self.completion_tokens,
            "total_tokens": self.prompt_tokens + self.completion_tokens,
            "llm_calls": self.llm_call_count,
            "search_calls": self.search_call_count,
            "scrape_calls": self.scrape_call_count,
            "estimated_cost_usd": self.calculate_cost(model_name),
        }
