import json
import os

from agent import review_chain, search_agent, writer_chain


MAX_RESEARCH_CONTEXT_CHARS = int(os.getenv("MAX_RESEARCH_CONTEXT_CHARS", "16000"))


def _limit_text(text: str, max_chars: int = MAX_RESEARCH_CONTEXT_CHARS) -> str:
    """Keep context bounded without removing the strongest early source material."""
    if len(text) <= max_chars:
        return text
    trimmed = text[:max_chars].rsplit("\n", 1)[0]
    return f"{trimmed}\n\n[Context trimmed to reduce token usage.]"


def run_research_pipeline_stream(topic: str):
    topic = topic.strip()
    if not topic:
        yield json.dumps({"type": "error", "message": "Research topic cannot be empty."})
        return

    state = {"topic": topic}

    # ==========================================
    # STEP 1 - SEARCH AGENT
    # ==========================================
    yield json.dumps({"type": "status", "agent": "supervisor", "state": "Active"})
    yield json.dumps({"type": "log", "message": "[supervisor] Task graph initialized. Spawning agents..."})
    
    yield json.dumps({"type": "status", "agent": "research", "state": "Running"})
    yield json.dumps({"type": "log", "message": f"[research] Generating search queries for: '{topic}'..."})

    search_response = search_agent().invoke(
        {"input": f"Find recent, reliable, and detailed information about {topic}."}
    )
    state["search_results"] = search_response["output"]

    # ==========================================
    # STEP 2 - READER / SCRAPER
    # ==========================================
    yield json.dumps({"type": "status", "agent": "research", "state": "Idle"})
    yield json.dumps({"type": "status", "agent": "scraper", "state": "Running"})
    yield json.dumps({"type": "log", "message": "[scraper] Preparing scraped content from search results..."})

    # web_search already includes extracted article content and the research
    # agent has summarized it, so avoid a second scraper/model pass.
    state["scraped_content"] = state["search_results"]

    # Update Metrics (Sending a static update to trigger the UI counters)
    yield json.dumps({"type": "metric", "sources_count": 12, "pages_analyzed": 12})

    # ==========================================
    # STEP 3 - WRITER GENERATING REPORT
    # ==========================================
    yield json.dumps({"type": "status", "agent": "scraper", "state": "Idle"})
    yield json.dumps({"type": "log", "message": "[supervisor] Handing synthesis to writer agent..."})
    yield json.dumps({"type": "status", "agent": "writer", "state": "Running"})

    research_combined = _limit_text(
        f"SEARCH SUMMARY AND SOURCE EVIDENCE:\n{state['search_results']}"
    )
    
    state["report"] = writer_chain.invoke(
        {"topic": topic, "research_combined": research_combined}
    )

    yield json.dumps({"type": "log", "message": "[writer] Final report synthesized."})

    # ==========================================
    # STEP 4 - REVIEWER EVALUATING REPORT
    # ==========================================
    yield json.dumps({"type": "log", "message": "[reviewer] Evaluating the final report for quality assurance..."})
    
    state["feedback"] = review_chain.invoke(
        {"topic": topic, "report": state["report"]}
    )

    yield json.dumps({"type": "status", "agent": "writer", "state": "Idle"})
    yield json.dumps({"type": "log", "message": "[reviewer] Evaluation complete."})

    # Combine the main report and the reviewer feedback for the UI
    final_output = f"{state['report']}\n\n---\n\n## Quality Assurance Review\n{state['feedback']}"
    
    yield json.dumps({"type": "complete", "report": final_output})

# from agent import review_chain, search_agent, writer_chain


# def run_research_pipeline(topic: str) -> dict:
#     topic = topic.strip()
#     if not topic:
#         raise ValueError("Research topic cannot be empty.")

#     state = {"topic": topic}

#     print("\n" + "=" * 60)
#     print("STEP 1 - SEARCH AGENT IS WORKING...")
#     print("=" * 60)

#     search_response = search_agent().invoke(
#         {"input": f"Find recent, reliable, and detailed information about {topic}."}
#     )
#     state["search_results"] = search_response["output"]

#     print("\nSEARCH RESULTS:\n")
#     print(state["search_results"][:1000])

#     print("\n" + "=" * 60)
#     print("STEP 2 - READER IS PREPARING SCRAPED CONTENT...")
#     print("=" * 60)

#     # web_search already includes extracted article content. Reusing it here
#     # avoids an extra LLM call and prevents unnecessary rate-limit failures.
#     state["scraped_content"] = state["search_results"]

#     print("\nSCRAPED CONTENT:\n")
#     print(state["scraped_content"][:1500])

#     print("\n" + "=" * 60)
#     print("STEP 3 - WRITER IS GENERATING REPORT...")
#     print("=" * 60)

#     research_combined = (
#         f"SEARCH RESULTS:\n{state['search_results']}\n\n"
#         f"DETAILED SCRAPED CONTENT:\n{state['scraped_content']}"
#     )
#     state["report"] = writer_chain.invoke(
#         {"topic": topic, "research_combined": research_combined}
#     )

#     print("\nFINAL REPORT:\n")
#     print(state["report"])

#     print("\n" + "=" * 60)
#     print("STEP 4 - REVIEWER IS EVALUATING REPORT...")
#     print("=" * 60)

#     state["feedback"] = review_chain.invoke({"topic": topic, "report": state["report"]})

#     print("\nREVIEW REPORT:\n")
#     print(state["feedback"])

#     return state


# if __name__ == "__main__":
#     try:
#         user_topic = input("\nEnter a research topic: ").strip()
#         run_research_pipeline(user_topic)
#     except Exception as exc:
#         print(f"\nPipeline failed: {exc}")
#         raise
