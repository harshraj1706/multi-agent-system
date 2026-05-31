from agent import review_chain, search_agent, writer_chain


def run_research_pipeline(topic: str) -> dict:
    topic = topic.strip()
    if not topic:
        raise ValueError("Research topic cannot be empty.")

    state = {"topic": topic}

    print("\n" + "=" * 60)
    print("STEP 1 - SEARCH AGENT IS WORKING...")
    print("=" * 60)

    search_response = search_agent().invoke(
        {"input": f"Find recent, reliable, and detailed information about {topic}."}
    )
    state["search_results"] = search_response["output"]

    print("\nSEARCH RESULTS:\n")
    print(state["search_results"][:1000])

    print("\n" + "=" * 60)
    print("STEP 2 - READER IS PREPARING SCRAPED CONTENT...")
    print("=" * 60)

    # web_search already includes extracted article content. Reusing it here
    # avoids an extra LLM call and prevents unnecessary rate-limit failures.
    state["scraped_content"] = state["search_results"]

    print("\nSCRAPED CONTENT:\n")
    print(state["scraped_content"][:1500])

    print("\n" + "=" * 60)
    print("STEP 3 - WRITER IS GENERATING REPORT...")
    print("=" * 60)

    research_combined = (
        f"SEARCH RESULTS:\n{state['search_results']}\n\n"
        f"DETAILED SCRAPED CONTENT:\n{state['scraped_content']}"
    )
    state["report"] = writer_chain.invoke(
        {"topic": topic, "research_combined": research_combined}
    )

    print("\nFINAL REPORT:\n")
    print(state["report"])

    print("\n" + "=" * 60)
    print("STEP 4 - REVIEWER IS EVALUATING REPORT...")
    print("=" * 60)

    state["feedback"] = review_chain.invoke({"topic": topic, "report": state["report"]})

    print("\nREVIEW REPORT:\n")
    print(state["feedback"])

    return state


if __name__ == "__main__":
    try:
        user_topic = input("\nEnter a research topic: ").strip()
        run_research_pipeline(user_topic)
    except Exception as exc:
        print(f"\nPipeline failed: {exc}")
        raise
