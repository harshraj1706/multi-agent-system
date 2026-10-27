"""
FastAPI application exposing REST and Server-Sent Events (SSE) streaming endpoints.
Fully backward-compatible with /api/research?topic=... while providing run management,
semantic search, and human-in-the-loop approvals.
"""

import json
import sys
from pathlib import Path
from typing import Optional

# Ensure src/ is on python path
src_path = str(Path(__file__).resolve().parent / "src")
if src_path not in sys.path:
    sys.path.insert(0, src_path)

import uvicorn
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from cognisynth.config import settings
from cognisynth.services.research_service import get_research_service
from cognisynth.services.approval_service import get_approval_service, ApprovalStatus
from cognisynth.memory.repository import get_repository
from cognisynth.memory.vector_store import get_vector_store
from cognisynth.evaluation.benchmark import run_offline_benchmark

app = FastAPI(
    title="CogniSynth API",
    description="Autonomous Research & Decision Intelligence Platform API",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class SemanticQueryRequest(BaseModel):
    query: str
    top_k: int = 4


class ApprovalDecisionRequest(BaseModel):
    status: ApprovalStatus
    feedback: Optional[str] = None
    modifications: Optional[dict] = None


@app.get("/api/health")
async def health():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "CogniSynth",
        "version": "1.0.0",
        "llm_model": settings.llm_model,
        "fallback_model": settings.llm_fallback_model,
    }


@app.get("/api/research")
async def research_endpoint(topic: str = Query(..., min_length=1)):
    """
    Main SSE streaming research endpoint (100% backward compatible).
    Emits data: {JSON}\n\n events.
    """
    service = get_research_service()

    def event_stream():
        for event in service.run_research_stream(topic):
            yield f"data: {event}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")


@app.get("/api/runs")
async def list_runs():
    """List all historical research runs."""
    repo = get_repository()
    return repo.list_runs()


@app.get("/api/runs/{run_id}")
async def get_run_details(run_id: str):
    """Get complete run record, metrics, and report."""
    repo = get_repository()
    run = repo.get_run(run_id)
    if not run:
        raise HTTPException(status_code=404, detail=f"Run '{run_id}' not found.")
    report_versions = repo.get_report_versions(run_id)
    return {"run": run, "versions": report_versions}


@app.post("/api/search/semantic")
async def semantic_search(request: SemanticQueryRequest):
    """Perform semantic search across previous research sessions in the vector store."""
    vs = get_vector_store()
    results = vs.similarity_search(request.query, top_k=request.top_k)
    return {"query": request.query, "matches": results}


@app.get("/api/benchmark")
async def run_benchmark():
    """Execute reproducible evaluation benchmark suite."""
    results = run_offline_benchmark()
    return {"benchmark_cases": len(results), "results": results}


@app.post("/api/approvals/{checkpoint_id}")
async def resolve_approval(checkpoint_id: str, decision: ApprovalDecisionRequest):
    """Approve, reject, or modify an active checkpoint."""
    approval_svc = get_approval_service()
    cp = approval_svc.resolve_checkpoint(
        checkpoint_id=checkpoint_id,
        status=decision.status,
        feedback=decision.feedback,
        modifications=decision.modifications,
    )
    if not cp:
        raise HTTPException(status_code=404, detail=f"Checkpoint '{checkpoint_id}' not found.")
    return cp.to_dict()


if __name__ == "__main__":
    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=False)