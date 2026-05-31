import os

from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain_core.messages import BaseMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_mistralai import ChatMistralAI

from tool import scrape_url, web_search

load_dotenv()


def _require_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(
            f"{name} is not set. Add it to your .env file before running the pipeline."
        )
    return value


_require_env("MISTRAL_API_KEY")

llm = ChatMistralAI(
    model_name=os.getenv("MISTRAL_MODEL", "mistral-large-latest"),
    temperature=float(os.getenv("MISTRAL_TEMPERATURE", "0.2")),
    max_tokens=int(os.getenv("MISTRAL_MAX_TOKENS", "1800")),
)


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


search_system_prompt = """
You are an expert Research Agent.

Your task is to search for comprehensive, reliable, and detailed
information about the given topic.

Use the web_search tool to find recent and relevant results.
Call the web_search tool once, then summarize the best evidence.
"""


def search_agent():
    agent = create_agent(
        model=llm,
        tools=[web_search],
        system_prompt=search_system_prompt,
    )
    return AgentRunner(agent, recursion_limit=5)


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
        model=llm,
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

writer_chain = writer_prompt | llm | StrOutputParser()


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

review_chain = review_prompt | llm | StrOutputParser()
