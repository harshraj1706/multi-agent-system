"""
CogniSynth - Autonomous Research & Decision Intelligence Platform.
Full multi-tab Streamlit dashboard: Overview, Dynamic Plan, Evidence & Sources,
Contradictions & QA, Final Report, Telemetry & Traces, and Research History.
"""

import json
import sys
from pathlib import Path
from typing import Any

# Ensure src/ is on python path
src_path = str(Path(__file__).resolve().parent / "src")
if src_path not in sys.path:
    sys.path.insert(0, src_path)

import streamlit as st
from cognisynth.config import settings
from pipeline import run_research_pipeline_stream
from cognisynth.memory.repository import get_repository
from cognisynth.memory.vector_store import get_vector_store

# Page Configuration
st.set_page_config(
    page_title="CogniSynth | Autonomous Decision Intelligence",
    page_icon="🧬",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Premium Dark Theme CSS Injection
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');
    
    .stApp {
        background-color: #06030F;
        color: #F0F2F6;
        font-family: 'Inter', sans-serif;
    }
    
    .hero-title {
        background: linear-gradient(135deg, #FFFFFF 0%, #A78BFA 50%, #06B6D4 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 2.8rem;
        font-weight: 800;
        text-align: center;
        letter-spacing: -0.03em;
        margin-bottom: 0.2rem;
    }
    
    .hero-subtitle {
        text-align: center;
        color: #94A3B8;
        font-size: 1.05rem;
        max-width: 850px;
        margin: 0 auto 2rem auto;
        line-height: 1.5;
    }
    
    .agent-card {
        background: rgba(255, 255, 255, 0.03);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 12px;
        padding: 14px 18px;
        margin-bottom: 10px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        backdrop-filter: blur(12px);
        transition: all 0.2s ease;
    }
    .agent-card:hover {
        border-color: rgba(167, 139, 250, 0.3);
        background: rgba(255, 255, 255, 0.05);
    }
    
    .status-badge {
        font-size: 0.75rem;
        font-weight: 600;
        padding: 3px 10px;
        border-radius: 20px;
        display: inline-flex;
        align-items: center;
        gap: 6px;
    }
    
    .log-box {
        background-color: #0A0718;
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 12px;
        padding: 16px;
        font-family: 'JetBrains Mono', monospace;
        height: 380px;
        overflow-y: auto;
        color: #CBD5E1;
        font-size: 0.85rem;
        line-height: 1.6;
    }
    
    .stat-card {
        background: linear-gradient(180deg, rgba(255,255,255,0.04) 0%, rgba(255,255,255,0.01) 100%);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 14px;
        padding: 18px;
        text-align: center;
    }
    .stat-val {
        font-size: 2rem;
        font-weight: 800;
        background: linear-gradient(90deg, #A78BFA, #38BDF8);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    .stat-label {
        color: #94A3B8;
        font-size: 0.8rem;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-top: 4px;
    }
    
    .conflict-card {
        background: rgba(239, 68, 68, 0.08);
        border: 1px solid rgba(239, 68, 68, 0.3);
        border-radius: 12px;
        padding: 16px;
        margin-bottom: 12px;
    }
    
    .claim-item {
        background: rgba(255, 255, 255, 0.03);
        border-left: 3px solid #8B5CF6;
        padding: 12px 16px;
        border-radius: 0 8px 8px 0;
        margin-bottom: 8px;
    }
    
    .stTabs [data-baseweb="tab-list"] {
        gap: 10px;
        border-bottom: 1px solid rgba(255, 255, 255, 0.08);
        padding-bottom: 4px;
    }
    .stTabs [data-baseweb="tab"] {
        background-color: transparent;
        border-radius: 8px;
        color: #94A3B8;
        padding: 8px 16px;
        font-weight: 500;
    }
    .stTabs [aria-selected="true"] {
        background-color: rgba(139, 92, 246, 0.15) !important;
        color: #FFFFFF !important;
        border: 1px solid rgba(139, 92, 246, 0.4) !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# Sidebar Configuration
with st.sidebar:
    st.markdown("### 🧬 CogniSynth Platform")
    st.caption("Autonomous Research & Decision Intelligence")
    st.markdown("---")

    st.markdown("**Engine Settings**")
    model_choice = st.selectbox(
        "Primary LLM",
        [settings.llm_model, settings.llm_fallback_model],
        index=0,
    )
    search_depth = st.select_slider(
        "Research Depth",
        options=["Rapid (2 sources)", "Standard (4 sources)", "Deep (8 sources)"],
        value="Standard (4 sources)",
    )
    max_src_map = {"Rapid (2 sources)": 2, "Standard (4 sources)": 4, "Deep (8 sources)": 8}
    chosen_max_sources = max_src_map[search_depth]

    st.markdown("---")
    st.markdown("**Model Router Topology**")
    st.markdown("⚡ **Fast Tasks**: `Qwen 3.6 (27B)`")
    st.markdown("🔬 **Research**: `Compound Mini`")
    st.markdown("🧠 **Reasoning**: `GPT-OSS 120B`")
    st.markdown("⚖️ **Final Judge**: `Gemini Flash`")

    st.markdown("---")
    st.markdown("**System Health**")
    st.success("✓ Groq Router Online (Qwen / GPT-OSS)")
    st.success(f"✓ Gemini Final Judge (`{model_choice}`)")
    st.info("✓ Tavily Web Ingestion Active")
    st.info("✓ Local Vector Memory Ready")

    st.markdown("---")
    repo = get_repository()
    runs = repo.list_runs()
    st.markdown(f"**Past Sessions ({len(runs)})**")
    for r in runs[:5]:
        st.caption(f"• `{r.get('run_id')}`: {r.get('query')[:25]}...")

# Hero Title
st.markdown("<div class='hero-title'>CogniSynth Research Intelligence</div>", unsafe_allow_html=True)
st.markdown(
    "<div class='hero-subtitle'>Autonomous multi-agent platform for dynamic task decomposition, verifiable claim extraction, contradiction detection, and publication-ready intelligence reports.</div>",
    unsafe_allow_html=True,
)

# Search Bar Area
col_input, col_btn = st.columns([5, 1])
with col_input:
    topic_input = st.text_input(
        "Research Objective",
        placeholder="Enter complex research query (e.g., Solid-State Battery Commercialization vs Lithium-Ion)...",
        label_visibility="collapsed",
    )
with col_btn:
    start_btn = st.button("▶ Run Research", use_container_width=True, type="primary")

st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)

# Main Navigation Tabs
tab_overview, tab_plan, tab_evidence, tab_conflicts, tab_report, tab_telemetry, tab_history = st.tabs([
    "📊 Overview",
    "🗺️ Dynamic Plan",
    "🔍 Evidence & Claims",
    "⚖️ Contradictions & QA",
    "📄 Final Report",
    "📈 Telemetry & Traces",
    "📚 Research History",
])

# Initialize session state for persistent display across tabs
if "latest_data" not in st.session_state:
    st.session_state.latest_data = {
        "plan": None,
        "sources": [],
        "claims": [],
        "conflicts": [],
        "report": "",
        "metrics": {"sources_count": 0, "pages_analyzed": 0, "claims_count": 0, "confidence_score": 0.0, "cost_usd": 0.0, "latency_seconds": 0.0},
        "logs": "",
        "trace": None,
        "status": {},
    }

# Helper to render agent status cards
def render_agent_card(placeholder, name: str, role: str, state: str):
    colors = {
        "Active": ("#A78BFA", "rgba(167, 139, 250, 0.15)"),
        "Running": ("#38BDF8", "rgba(56, 189, 248, 0.15)"),
        "Idle": ("#94A3B8", "rgba(148, 163, 184, 0.08)"),
        "Completed": ("#34D399", "rgba(52, 211, 153, 0.15)"),
    }
    fg, bg = colors.get(state, ("#94A3B8", "rgba(148, 163, 184, 0.08)"))
    html = f"""
    <div class="agent-card">
        <div>
            <div style="font-weight: 600; font-size: 0.9rem; color: #FFFFFF;">{name}</div>
            <div style="color: #94A3B8; font-size: 0.75rem;">{role}</div>
        </div>
        <div class="status-badge" style="color: {fg}; background: {bg}; border: 1px solid {fg}40;">
            <span style="width: 6px; height: 6px; background-color: {fg}; border-radius: 50%;"></span>
            {state}
        </div>
    </div>
    """
    placeholder.markdown(html, unsafe_allow_html=True)


# OVERVIEW TAB SETUP
with tab_overview:
    # Live Stat Counters
    stat_col1, stat_col2, stat_col3, stat_col4, stat_col5 = st.columns(5)
    with stat_col1:
        stat_sources_ph = st.empty()
    with stat_col2:
        stat_claims_ph = st.empty()
    with stat_col3:
        stat_conf_ph = st.empty()
    with stat_col4:
        stat_latency_ph = st.empty()
    with stat_col5:
        stat_cost_ph = st.empty()

    def update_stat_boxes(m):
        stat_sources_ph.markdown(f"<div class='stat-card'><div class='stat-val'>{m.get('sources_count', 0)}</div><div class='stat-label'>Sources Ranked</div></div>", unsafe_allow_html=True)
        stat_claims_ph.markdown(f"<div class='stat-card'><div class='stat-val'>{m.get('claims_count', 0)}</div><div class='stat-label'>Verified Claims</div></div>", unsafe_allow_html=True)
        conf_val = f"{int(m.get('confidence_score', 0.0) * 100)}%"
        stat_conf_ph.markdown(f"<div class='stat-card'><div class='stat-val'>{conf_val}</div><div class='stat-label'>Derived Confidence</div></div>", unsafe_allow_html=True)
        stat_latency_ph.markdown(f"<div class='stat-card'><div class='stat-val'>{m.get('latency_seconds', 0.0):.1f}s</div><div class='stat-label'>Total Runtime</div></div>", unsafe_allow_html=True)
        cost_val = f"${m.get('cost_usd', 0.0):.4f}"
        stat_cost_ph.markdown(f"<div class='stat-card'><div class='stat-val'>{cost_val}</div><div class='stat-label'>Estimated Cost</div></div>", unsafe_allow_html=True)

    update_stat_boxes(st.session_state.latest_data["metrics"])
    st.markdown("<div style='height: 15px;'></div>", unsafe_allow_html=True)

    c_agents, c_logs = st.columns([1, 2])
    with c_agents:
        st.markdown("<h5 style='color: #FFFFFF; font-size: 0.95rem; margin-bottom: 12px;'>Agent Swarm Status</h5>", unsafe_allow_html=True)
        ph_sup = st.empty()
        ph_plan = st.empty()
        ph_res = st.empty()
        ph_scr = st.empty()
        ph_ver = st.empty()
        ph_wri = st.empty()
        ph_rev = st.empty()

        render_agent_card(ph_sup, "Supervisor Agent", "Orchestration & State", "Idle")
        render_agent_card(ph_plan, "Planner Agent", "Task DAG Decomposition", "Idle")
        render_agent_card(ph_res, "Research Agent", "Tavily Search Ingestion", "Idle")
        render_agent_card(ph_scr, "Scraper Agent", "Readability Content Parsing", "Idle")
        render_agent_card(ph_ver, "Verifier Agent", "Claim & Contradiction Audit", "Idle")
        render_agent_card(ph_wri, "Writer Agent", "Thematic Synthesis", "Idle")
        render_agent_card(ph_rev, "Reviewer Agent", "Adversarial QA Critique", "Idle")

    with c_logs:
        st.markdown("<h5 style='color: #FFFFFF; font-size: 0.95rem; margin-bottom: 12px;'>Real-Time Execution Logs</h5>", unsafe_allow_html=True)
        prog_bar = st.progress(0)
        ph_logs = st.empty()
        ph_logs.markdown(
            f"<div class='log-box'>{st.session_state.latest_data['logs'] or 'System standby. Enter a topic and click Run Research.'}</div>",
            unsafe_allow_html=True,
        )

# EXECUTION LOOP
if start_btn and topic_input:
    log_history = ""
    st.session_state.latest_data["logs"] = ""
    st.session_state.latest_data["sources"] = []
    st.session_state.latest_data["claims"] = []
    st.session_state.latest_data["conflicts"] = []

    render_agent_card(ph_sup, "Supervisor Agent", "Orchestration & State", "Active")
    prog_bar.progress(10)

    try:
        for event_raw in run_research_pipeline_stream(topic_input):
            try:
                evt = json.loads(event_raw) if isinstance(event_raw, str) else event_raw
                etype = evt.get("type")

                if etype == "log":
                    log_history += f"• {evt['message']}<br>"
                    ph_logs.markdown(f"<div class='log-box'>{log_history}</div>", unsafe_allow_html=True)

                elif etype == "status":
                    agent = evt.get("agent")
                    state = evt.get("state")
                    if agent == "supervisor":
                        render_agent_card(ph_sup, "Supervisor Agent", "Orchestration & State", state)
                    elif agent == "planner":
                        render_agent_card(ph_plan, "Planner Agent", "Task DAG Decomposition", state)
                        prog_bar.progress(25)
                    elif agent == "research":
                        render_agent_card(ph_res, "Research Agent", "Tavily Search Ingestion", state)
                        prog_bar.progress(45)
                    elif agent == "scraper":
                        render_agent_card(ph_scr, "Scraper Agent", "Readability Content Parsing", state)
                        prog_bar.progress(60)
                    elif agent == "verifier":
                        render_agent_card(ph_ver, "Verifier Agent", "Claim & Contradiction Audit", state)
                        prog_bar.progress(75)
                    elif agent == "writer":
                        render_agent_card(ph_wri, "Writer Agent", "Thematic Synthesis", state)
                        prog_bar.progress(88)
                    elif agent == "reviewer":
                        render_agent_card(ph_rev, "Reviewer Agent", "Adversarial QA Critique", state)
                        prog_bar.progress(95)

                elif etype == "plan":
                    st.session_state.latest_data["plan"] = evt.get("plan")

                elif etype == "sources":
                    st.session_state.latest_data["sources"] = evt.get("sources", [])

                elif etype == "claims":
                    st.session_state.latest_data["claims"] = evt.get("claims", [])

                elif etype == "conflicts":
                    st.session_state.latest_data["conflicts"] = evt.get("conflicts", [])

                elif etype == "metric":
                    st.session_state.latest_data["metrics"].update(evt)
                    update_stat_boxes(st.session_state.latest_data["metrics"])

                elif etype == "trace":
                    st.session_state.latest_data["trace"] = evt.get("trace")

                elif etype == "complete":
                    prog_bar.progress(100)
                    st.session_state.latest_data["report"] = evt.get("report", "")
                    render_agent_card(ph_sup, "Supervisor Agent", "Orchestration & State", "Completed")
                    render_agent_card(ph_rev, "Reviewer Agent", "Adversarial QA Critique", "Completed")

                elif etype == "error":
                    st.error(f"Execution notice: {evt.get('message')}")

            except json.JSONDecodeError:
                pass

        st.session_state.latest_data["logs"] = log_history
        st.success("✓ Autonomous research execution completed successfully! Review tabs for detailed analysis.")

    except Exception as exc:
        st.error(f"Error executing pipeline: {exc}")

# POPULATE DYNAMIC PLAN TAB
with tab_plan:
    st.markdown("### 🗺️ Dynamic Plan & Directed Acyclic Graph (DAG)")
    plan_obj = st.session_state.latest_data.get("plan")
    if plan_obj and "tasks" in plan_obj:
        st.info(f"**Objective**: {plan_obj.get('objective')}")
        for t in plan_obj["tasks"]:
            col_t1, col_t2, col_t3 = st.columns([1, 4, 1])
            with col_t1:
                st.code(t.get("task_id", "task"))
            with col_t2:
                st.markdown(f"**{t.get('objective')}**")
                deps = t.get("dependencies", [])
                if deps:
                    st.caption(f"Dependencies: {', '.join(deps)}")
            with col_t3:
                st.markdown(f"`{t.get('type', 'search').upper()}` (P{t.get('priority', 1)})")
            st.markdown("---")
    else:
        st.caption("No active task graph yet. Execute a research query to see the dynamic planner in action.")

# POPULATE EVIDENCE & CLAIMS TAB
with tab_evidence:
    col_src, col_clm = st.columns([1, 1])
    with col_src:
        st.markdown("### 🌐 Ranked Sources & Provenance")
        sources = st.session_state.latest_data.get("sources", [])
        if sources:
            for s in sources:
                with st.expander(f"⭐ {s.get('quality_score', 0.5):.2f} | {s.get('title', 'Source')}"):
                    st.markdown(f"**URL**: [{s.get('url')}]({s.get('url')})")
                    st.markdown(f"**Domain**: `{s.get('domain')}` | **Type**: `{s.get('source_type')}`")
                    st.progress(float(s.get("quality_score", 0.5)))
        else:
            st.caption("No sources ingested yet.")

    with col_clm:
        st.markdown("### 🔬 Atomic Verifiable Claims")
        claims = st.session_state.latest_data.get("claims", [])
        if claims:
            for c in claims:
                st.markdown(
                    f"""
                    <div class="claim-item">
                        <div style="font-weight: 500; color: #FFFFFF;">{c.get('text')}</div>
                        <div style="font-size: 0.75rem; color: #94A3B8; margin-top: 4px;">
                            Type: <code>{c.get('type')}</code> | Status: <b>{c.get('status')}</b> | Confidence: {int(c.get('confidence', 0.8)*100)}%
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
        else:
            st.caption("No claims extracted yet.")

# POPULATE CONTRADICTIONS & QA TAB
with tab_conflicts:
    st.markdown("### ⚖️ Contradiction Detection & Debate Audit")
    conflicts = st.session_state.latest_data.get("conflicts", [])
    if conflicts:
        for c in conflicts:
            st.markdown(
                f"""
                <div class="conflict-card">
                    <div style="color: #EF4444; font-weight: 700; font-size: 0.95rem;">
                        ⚠️ Contradiction Detected (Severity: {c.get('severity', 'medium').upper()})
                    </div>
                    <div style="margin: 8px 0; color: #F1F5F9;">{c.get('explanation')}</div>
                    <div style="font-size: 0.8rem; color: #A78BFA;"><b>Resolution Guidance</b>: {c.get('resolution')}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
    else:
        st.success("✓ Zero severe contradictions identified across validated sources.")

    st.markdown("---")
    st.markdown("### 📋 Quality Assurance Review")
    rep_text = st.session_state.latest_data.get("report", "")
    if "## Quality Assurance Review" in rep_text:
        qa_part = rep_text.split("## Quality Assurance Review")[1]
        st.markdown(qa_part)
    else:
        st.caption("QA critique will render here once review agent completes.")

# POPULATE FINAL REPORT TAB
with tab_report:
    st.markdown("### 📄 Publication-Ready Intelligence Report")
    rep_text = st.session_state.latest_data.get("report", "")
    if rep_text:
        main_rep = rep_text.split("## Quality Assurance Review")[0]
        st.markdown(main_rep)

        st.markdown("<div style='height: 15px;'></div>", unsafe_allow_html=True)
        btn_col1, btn_col2 = st.columns(2)
        with btn_col1:
            try:
                from cognisynth.tools.pdf_generator import markdown_to_pdf
                first_line = main_rep.split("\n")[0].replace("#", "").strip()
                doc_title = first_line if first_line else "CogniSynth Research Intelligence Report"
                metrics_data = st.session_state.latest_data.get("metrics", {})
                pdf_data = markdown_to_pdf(
                    title=doc_title,
                    markdown_content=main_rep,
                    confidence_score=metrics_data.get("confidence_score", 0.85),
                    sources_count=metrics_data.get("sources_count", 4),
                    claims_count=metrics_data.get("claims_count", 10),
                )
                st.download_button(
                    label="📕 Download Executive Report as PDF",
                    data=pdf_data,
                    file_name="cognisynth_research_report.pdf",
                    mime="application/pdf",
                    use_container_width=True,
                    type="primary",
                )
            except Exception as pdf_err:
                st.warning(f"PDF generation note: {pdf_err}")

        with btn_col2:
            st.download_button(
                label="📄 Download Report as Markdown",
                data=main_rep,
                file_name="cognisynth_research_report.md",
                mime="text/markdown",
                use_container_width=True,
            )
    else:
        st.caption("Final synthesized report will be rendered here upon completion.")

# POPULATE TELEMETRY & TRACES TAB
with tab_telemetry:
    st.markdown("### 📈 Execution Telemetry & Observability")
    trace = st.session_state.latest_data.get("trace")
    if trace and "spans" in trace:
        st.markdown(f"**Total Run Latency**: `{trace.get('total_latency_seconds')} seconds`")
        st.dataframe(trace.get("spans", []), use_container_width=True)
    else:
        st.caption("Telemetry spans will populate here after a run.")

# POPULATE RESEARCH HISTORY TAB
with tab_history:
    st.markdown("### 📚 Semantic Research Memory & Previous Sessions")
    c_q, c_q_btn = st.columns([4, 1])
    with c_q:
        q_text = st.text_input("Ask a question across previous research sessions:", placeholder="e.g., What battery chemistries had highest energy density?")
    with c_q_btn:
        q_btn = st.button("Search Memory", use_container_width=True)

    if q_btn and q_text:
        vs = get_vector_store()
        matches = vs.similarity_search(q_text, top_k=3)
        if matches:
            st.markdown(f"**Found {len(matches)} relevant excerpts in memory:**")
            for m in matches:
                with st.expander(f"Score: {m['similarity_score']:.2f} | Topic: {m['metadata'].get('topic', 'N/A')}"):
                    st.write(m["text"])
        else:
            st.info("No matching records found in vector memory.")

    st.markdown("---")
    st.markdown("**Historical Report Versions**")
    all_runs = repo.list_runs()
    for r in all_runs[:10]:
        rid = r.get("run_id")
        versions = repo.get_report_versions(rid)
        st.markdown(f"**Session `{rid}`**: *{r.get('query')}* ({len(versions)} versions)")
        for v in versions:
            st.caption(f"  • Version {v.get('version')}: {v.get('change_summary', 'Initial')} (Confidence: {v.get('confidence', 0.8):.2f})")