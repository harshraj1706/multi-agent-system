"""
Dynamic conditional router for LangGraph state machine.
"""

from cognisynth.graph.state import ResearchGraphState


def route_after_planning(state: ResearchGraphState) -> str:
    """Route to approval gate or directly to research execution."""
    if state.get("requires_approval") and not state.get("is_approved"):
        return "await_plan_approval"
    return "execute_research_tasks"


def route_after_verification(state: ResearchGraphState) -> str:
    """Check if claims were verified and confidence is sufficient for synthesis."""
    if state.get("errors"):
        return "error_handler"
    return "synthesize_report"


def route_after_critique(state: ResearchGraphState) -> str:
    """Check if report passed review or needs refinement."""
    return "finalize_run"
