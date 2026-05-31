import streamlit as st
import requests
import json

# Page Configuration
st.set_page_config(page_title="Agentic Research AI", layout="wide", initial_sidebar_state="collapsed")

# Premium Dark Theme CSS Injection
st.markdown("""
    <style>
    .stApp { background-color: #05010F; color: #FFFFFF; font-family: 'Inter', sans-serif; }
    .hero-title { background: linear-gradient(90deg, #FFFFFF, #7f22fe); -webkit-background-clip: text; -webkit-text-fill-color: transparent; font-size: 3rem; font-weight: bold; text-align: center; padding-top: 2rem;}
    .agent-card { background-color: rgba(255,255,255,0.05); border: 1px solid rgba(255,255,255,0.1); border-radius: 12px; padding: 15px; margin-bottom: 10px; display: flex; justify-content: space-between; align-items: center; backdrop-filter: blur(10px);}
    .log-box { background-color: rgba(0,0,0,0.5); border: 1px solid rgba(255,255,255,0.1); border-radius: 12px; padding: 15px; font-family: monospace; height: 280px; overflow-y: auto; color: #9f9fa9; font-size: 0.85rem;}
    .metric-box { background: rgba(255,255,255,0.05); padding: 15px; border-radius: 10px; border: 1px solid rgba(255,255,255,0.1); }
    .stTextInput>div>div>input { background-color: #1A1A24 !important; color: #FFFFFF !important; border: 1px solid rgba(255,255,255,0.1) !important; border-radius: 10px; }
    .stButton>button { background-color: #7f22fe !important; color: white !important; border-radius: 10px; border: none; box-shadow: 0 0 15px rgba(127, 34, 254, 0.5); width: 100%; font-weight: bold;}
    </style>
""", unsafe_allow_html=True)

# Helper function to dynamically draw agent status cards
def update_agent_card(placeholder, name, role, state, color):
    html = f"""
    <div class="agent-card">
        <div>
            <div style="font-weight: 600; font-size: 14px;">{name}</div>
            <div style="color: #9f9fa9; font-size: 12px;">{role}</div>
        </div>
        <div style="color: {color}; font-size: 12px; display: flex; align-items: center; gap: 5px;">
            <div style="width: 8px; height: 8px; background-color: {color}; border-radius: 50%; box-shadow: 0 0 8px {color};"></div>
            {state}
        </div>
    </div>
    """
    placeholder.markdown(html, unsafe_allow_html=True)

# UI: Hero Section
st.markdown("<div class='hero-title'>Production-grade AI Research Platform</div>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: #9f9fa9;'>Deploy a coordinated swarm of agents to discover sources, scrape the web, and synthesize publishable reports in real time.</p>", unsafe_allow_html=True)

search_col, btn_col = st.columns([5, 1])
with search_col:
    topic = st.text_input("", placeholder="Enter a research topic...", label_visibility="collapsed")
with btn_col:
    run_btn = st.button("▶ Run Research")

st.markdown("---")

# UI: Main Dashboard Layout
col1, col2, col3 = st.columns([1, 2, 1])

with col1:
    st.markdown("<h4 style='color: white; font-size: 16px;'>Agent Execution Status</h4>", unsafe_allow_html=True)
    sup_ph = st.empty()
    res_ph = st.empty()
    scr_ph = st.empty()
    wri_ph = st.empty()
    
    # Render Default Idle States
    update_agent_card(sup_ph, "Supervisor Agent", "Coordinating tasks", "Idle", "#9f9fa9")
    update_agent_card(res_ph, "Research Agent", "Querying sources", "Idle", "#9f9fa9")
    update_agent_card(scr_ph, "Scraper Agent", "Fetching pages", "Idle", "#9f9fa9")
    update_agent_card(wri_ph, "Writer Agent", "Synthesizing report", "Idle", "#9f9fa9")

with col2:
    st.markdown("<h4 style='color: white; font-size: 16px;'>Real-time Execution Logs</h4>", unsafe_allow_html=True)
    progress_bar = st.progress(0)
    log_ph = st.empty()
    log_ph.markdown("<div class='log-box'>Awaiting task initialization...</div>", unsafe_allow_html=True)

with col3:
    st.markdown("<h4 style='color: white; font-size: 16px;'>Sources Discovered</h4>", unsafe_allow_html=True)
    metric_ph = st.empty()
    metric_ph.markdown("""
    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px;">
        <div class="metric-box">
            <div style="color: #7f22fe; font-size: 24px; font-weight: bold;">0</div>
            <div style="color: #9f9fa9; font-size: 12px;">URLs collected</div>
        </div>
        <div class="metric-box">
            <div style="color: #00d2ff; font-size: 24px; font-weight: bold;">0</div>
            <div style="color: #9f9fa9; font-size: 12px;">Pages analyzed</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("---")
st.markdown("<h4 style='color: white; font-size: 16px;'>Final Generated Report</h4>", unsafe_allow_html=True)
report_ph = st.empty()

# Logic: Execution and Real-Time State Updates
if run_btn and topic:
    log_accumulator = ""
    agent_colors = {"Active": "#7f22fe", "Running": "#00d2ff", "Idle": "#9f9fa9"}
    
    # Establish connection to FastAPI Backend
    with requests.get(f"http://localhost:8000/api/research?topic={topic}", stream=True) as r:
        for line in r.iter_lines():
            if line:
                decoded = line.decode('utf-8')
                if decoded.startswith("data: "):
                    try:
                        data = json.loads(decoded[6:])
                        event_type = data.get("type")
                        
                        # 1. Update Logs
                        if event_type == "log":
                            log_accumulator += data['message'] + "<br><br>"
                            log_ph.markdown(f"<div class='log-box'>{log_accumulator}</div>", unsafe_allow_html=True)
                        
                        # 2. Update Agent Status & Progress Bar
                        elif event_type == "status":
                            a = data['agent']
                            s = data['state']
                            c = agent_colors.get(s, "#9f9fa9")
                            
                            if a == "supervisor":
                                update_agent_card(sup_ph, "Supervisor Agent", "Coordinating tasks", s, c)
                            elif a == "research":
                                update_agent_card(res_ph, "Research Agent", "Querying sources", s, c)
                                progress_bar.progress(33)
                            elif a == "scraper":
                                update_agent_card(scr_ph, "Scraper Agent", "Fetching pages", s, c)
                                progress_bar.progress(66)
                            elif a == "writer":
                                update_agent_card(wri_ph, "Writer Agent", "Synthesizing report", s, c)
                                progress_bar.progress(90)
                        
                        # 3. Update Metrics
                        elif event_type == "metric":
                            metric_ph.markdown(f'''
                            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px;">
                                <div class="metric-box">
                                    <div style="color: #7f22fe; font-size: 24px; font-weight: bold;">{data['sources_count']}</div>
                                    <div style="color: #9f9fa9; font-size: 12px;">URLs collected</div>
                                </div>
                                <div class="metric-box">
                                    <div style="color: #00d2ff; font-size: 24px; font-weight: bold;">{data['pages_analyzed']}</div>
                                    <div style="color: #9f9fa9; font-size: 12px;">Pages analyzed</div>
                                </div>
                            </div>
                            ''', unsafe_allow_html=True)
                        
                        # 4. Render Final Output
                        elif event_type == "complete":
                            progress_bar.progress(100)
                            report_ph.markdown(data['report'])
                            
                    except json.JSONDecodeError:
                        pass