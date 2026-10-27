"""
LangGraph Workflow Builder for CogniSynth.
Assembles the multi-agent execution graph with dynamic task dispatch and state transitions.
"""

from langgraph.graph import StateGraph, END
from cognisynth.graph.state import ResearchGraphState
from cognisynth.agents.planner import PlannerAgent
from cognisynth.agents.researcher import ResearcherAgent
from cognisynth.agents.analyst import AnalystAgent
from cognisynth.agents.verifier import VerifierAgent
from cognisynth.agents.critic import CriticAgent
from cognisynth.agents.reporter import ReporterAgent
from cognisynth.evidence.extractor import extract_claims_and_evidence


def build_research_graph():
    """
    Construct the state graph connecting planner -> research -> extraction -> verification -> analyst -> reporter -> critic.
    """
    workflow = StateGraph(ResearchGraphState)

    # Instantiate agents
    planner = PlannerAgent()
    researcher = ResearcherAgent()
    analyst = AnalystAgent()
    verifier = VerifierAgent()
    reporter = ReporterAgent()
    critic = CriticAgent()

    # 1. Planner Node
    def plan_node(state: ResearchGraphState) -> dict:
        query = state.get("query", "")
        plan = planner.plan(query)
        return {
            "plan": plan,
            "current_step": "planning_completed",
            "status": "planned",
        }

    # 2. Research Tasks Node
    def research_node(state: ResearchGraphState) -> dict:
        plan = state.get("plan")
        sources = list(state.get("sources", []))
        documents = list(state.get("documents", []))

        if plan:
            search_tasks = [t for t in plan.tasks if t.type.value == "search"]
            for task in search_tasks:
                task_srcs, task_docs = researcher.execute_task(task, max_results=3)
                sources.extend(task_srcs)
                documents.extend(task_docs)

        # Deduplicate sources by URL
        seen_urls = set()
        unique_sources = []
        for s in sources:
            if s.url not in seen_urls:
                seen_urls.add(s.url)
                unique_sources.append(s)

        return {
            "sources": unique_sources,
            "documents": documents,
            "current_step": "research_completed",
            "status": "researched",
        }

    # 3. Claim & Evidence Extraction Node
    def extraction_node(state: ResearchGraphState) -> dict:
        sources = state.get("sources", [])
        documents = state.get("documents", [])
        doc_map = {d.source_id: d for d in documents}

        all_claims = []
        all_evidence = []

        for src in sources[:4]:
            doc = doc_map.get(src.source_id)
            if doc:
                c_list, e_list = extract_claims_and_evidence(src, doc, use_llm=True)
                all_claims.extend(c_list)
                all_evidence.extend(e_list)

        return {
            "claims": all_claims,
            "evidence_items": all_evidence,
            "current_step": "extraction_completed",
        }

    # 4. Verification & Contradiction Node
    def verification_node(state: ResearchGraphState) -> dict:
        claims = state.get("claims", [])
        evidence_items = state.get("evidence_items", [])
        sources = state.get("sources", [])

        ver_results, conflicts, confidence, rationale = verifier.verify_research(
            claims, evidence_items, sources
        )

        return {
            "conflicts": conflicts,
            "confidence_score": confidence,
            "confidence_rationale": rationale,
            "current_step": "verification_completed",
        }

    # 5. Analyst Node
    def analysis_node(state: ResearchGraphState) -> dict:
        query = state.get("query", "")
        claims = state.get("claims", [])
        sources = state.get("sources", [])
        docs = state.get("documents", [])

        analysis_text = analyst.analyze(query, claims, sources, docs)
        return {
            "report_content": analysis_text,
            "current_step": "analysis_completed",
        }

    # 6. Reporter Node
    def report_node(state: ResearchGraphState) -> dict:
        run_id = state.get("run_id", "run_local")
        query = state.get("query", "")
        analysis_text = state.get("report_content", "")
        claims = state.get("claims", [])
        sources = state.get("sources", [])
        conflicts = state.get("conflicts", [])
        confidence = state.get("confidence_score", 0.8)
        rationale = state.get("confidence_rationale", "")

        rep = reporter.generate_report(
            run_id=run_id,
            query=query,
            analysis_text=analysis_text,
            claims=claims,
            sources=sources,
            conflicts=conflicts,
            confidence_score=confidence,
            confidence_rationale=rationale,
        )

        return {
            "report_content": rep.content,
            "current_step": "report_completed",
        }

    # 7. Critic QA Node
    def critic_node(state: ResearchGraphState) -> dict:
        query = state.get("query", "")
        report_content = state.get("report_content", "")
        conflicts = state.get("conflicts", [])
        confidence = state.get("confidence_score", 0.8)

        qa = critic.review(query, report_content, conflicts, confidence)
        return {
            "qa_review": qa,
            "status": "completed",
            "current_step": "all_completed",
        }

    # Register Nodes
    workflow.add_node("planner", plan_node)
    workflow.add_node("researcher", research_node)
    workflow.add_node("extractor", extraction_node)
    workflow.add_node("verifier", verification_node)
    workflow.add_node("analyst", analysis_node)
    workflow.add_node("reporter", report_node)
    workflow.add_node("critic", critic_node)

    # Connect Edges
    workflow.set_entry_point("planner")
    workflow.add_edge("planner", "researcher")
    workflow.add_edge("researcher", "extractor")
    workflow.add_edge("extractor", "verifier")
    workflow.add_edge("verifier", "analyst")
    workflow.add_edge("analyst", "reporter")
    workflow.add_edge("reporter", "critic")
    workflow.add_edge("critic", END)

    return workflow.compile()
