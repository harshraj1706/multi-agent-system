"""
Agent definitions and legacy compatibility adapter.
Preserves GeminiChatModel, chains, runners, and retry behavior while linking into cognisynth.
"""

import sys
from pathlib import Path
from functools import lru_cache
from typing import Any

# Ensure src/ is on python path
src_path = str(Path(__file__).resolve().parent / "src")
if src_path not in sys.path:
    sys.path.insert(0, src_path)

from langchain_core.messages import AIMessage, BaseMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import Runnable
from cognisynth.tools.llm import GeminiChatModel, get_default_llm, _message_text
from cognisynth.config import settings
from tool import scrape_url, web_search


class LazyChain:
    """Wrapper that preserves `.invoke()` while delaying API setup."""

    def __init__(self, prompt: ChatPromptTemplate):
        self.prompt = prompt

    @lru_cache(maxsize=1)
    def _chain(self):
        return self.prompt | get_default_llm() | StrOutputParser()

    def invoke(self, inputs: dict) -> str:
        return self._chain().invoke(inputs)


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


def search_agent():
    return DirectSearchRunner(web_search)


def reader_agent():
    from langchain.agents import create_agent
    agent = create_agent(
        model=get_default_llm(),
        tools=[scrape_url],
        system_prompt="You are an expert Web Content Extraction Agent.",
    )
    return AgentRunner(agent, recursion_limit=6)


writer_prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "You are an expert Research Analyst. Synthesize a comprehensive, accurate research report.",
        ),
        (
            "human",
            "Research Topic: {topic}\n\nResearch Data:\n{research_combined}\n\nGenerate a complete research report.",
        ),
    ]
)

writer_chain = LazyChain(writer_prompt)

review_prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "You are an expert Quality Assurance Reviewer. Score the report 1-10, list strengths, weaknesses, and a final verdict.",
        ),
        (
            "human",
            "Research Topic: {topic}\n\nReport:\n{report}\n\nEvaluate this report.",
        ),
    ]
)

review_chain = LazyChain(review_prompt)
