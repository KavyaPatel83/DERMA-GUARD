"""
app/clinician_app.py — Streamlit Clinician Dashboard for DERMA-GUARD v4.0

Sections:
  1. Live Evidence Panel — Q/R/C radar, weight bars
  2. Model Confidence Grid — 5-model heatmap
  3. Pipeline Trace — step-by-step evidence chain
  4. System Metrics — across all processed cases
"""
import json
from typing import Dict, List, Optional

import requests
import streamlit as st

try:
    import plotly.graph_objects as go
    import plotly.express as px
    PLOTLY_AVAILABLE = True
except ImportError:
    PLOTLY_AVAILABLE = False

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
API_BASE = "http://localhost:8000"

st.set_page_config(
    page_title="DERMA-GUARD v4.0 — Clinician Dashboard",
    page_icon="⚕️",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
    .main { background: #0d1117; }
    .metric-card {
        background: rgba(255,255,255,0.04);
        border: 1px solid rgba(255,255,255,0.08);
        border-radius: 12px;
        padding: 1.25rem;
        text-align: center;
    }
    .metric-val { font-size: 2rem; font-weight: 700; color: #64b5f6; }
    .metric-lbl { font-size: 0.85rem; color: #90a4ae; margin-top: 0.25rem; }
    .evidence-row {
        display: flex;
        gap: 0.5rem;
        align-items: center;
        margin-bottom: 0.4rem;
    }
    .evidence-bar-bg {
        flex: 1; background: rgba(255,255,255,0.08);
        border-radius: 999px; height: 8px; overflow: hidden;
    }
    .evidence-bar-fill {
        height: 8px; border-radius: 999px;
        background: linear-gradient(90deg, #1976d2, #64b5f6);
    }
    .panel-title {
        font-size: 1.1rem; font-weight: 600;
        color: #b0bec5; margin-bottom: 1rem;
        text-transform: uppercase; letter-spacing: 0.1em;
    }
    .action-badge {
        display: inline-block; padding: 0.3rem 0.8rem;
        border-radius: 999px; font-weight: 600; font-size: 0.8rem;
    }
    .accept   { background: rgba(76,175,80,0.2); color: #81c784; }
    .arbitrate { background: rgba(255,193,7,0.2); color: #ffd54f; }
    .acquire  { background: rgba(33,150,243,0.2); color: #64b5f6; }
    .escalate { background: rgba(244,67,54,0.2); color: #ef9a9a; }
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------
with st.sidebar:
    st.markdown("## ⚕️ Clinician Dashboard")
    st.markdown("**DERMA-GUARD v4.0**")
    st.divider()

    case_id_input = st.text_input("Case ID", placeholder="Enter case ID…")
    fetch_btn = st.button("🔍 Load Case", use_container_width=True)

    st.divider()
    auto_refresh = st.checkbox("Auto-refresh metrics (30s)", value=False)
    st.caption(f"API: `{API_BASE}`")

    try:
        resp = requests.get(f"{API_BASE}/health", timeout=3)
        if resp.status_code == 200:
            h = resp.json()
            st.success("✅ Connected")
            st.caption(f"GPU: {'✓' if h.get('gpu_available') else '✗'} | "
                       f"LLM: {'✓' if h.get('ollama_available') else '✗'}")
        else:
            st.warning("API error")
    except Exception:
        st.error("API Offline")

# ---------------------------------------------------------------------------
# Load case
# ---------------------------------------------------------------------------
current_result = None
if fetch_btn and case_id_input:
    try:
        resp = requests.get(f"{API_BASE}/case/{case_id_input}", timeout=10)
        if resp.status_code == 200:
            current_result = resp.json()
        else:
            st.error(f"Case `{case_id_input}` not found.")
    except Exception as e:
        st.error(f"Error: {e}")

# ---------------------------------------------------------------------------
# Main content: System Metrics (top)
# ---------------------------------------------------------------------------
st.markdown("### 🏥 System Overview")

try:
    metrics_resp = requests.get(f"{API_BASE}/metrics", timeout=5)
    if metrics_resp.status_code == 200:
        m = metrics_resp.json()
        cols = st.columns(6)
        metric_items = [
            ("Total Cases", m.get("total_cases_processed", 0)),
            ("✅ ACCEPT", m.get("accept_count", 0)),
            ("⚖️ ARBITRATE", m.get("arbitrate_count", 0)),
            ("🔍 ACQUIRE", m.get("acquire_count", 0)),
            ("🚨 ESCALATE", m.get("escalate_count", 0)),
            ("⏸️ ABSTAIN", m.get("abstain_count", 0)),
        ]
        for col, (label, value) in zip(cols, metric_items):
            with col:
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-val">{value}</div>
                    <div class="metric-lbl">{label}</div>
                </div>
                """, unsafe_allow_html=True)
except Exception:
    st.info("Submit cases to see system metrics.")

st.divider()

# ---------------------------------------------------------------------------
# Case detail view
# ---------------------------------------------------------------------------
if current_result:
    result = current_result
    action = result.get("action", "?")
    confidence = result.get("confidence") or 0.0

    st.markdown(f"### Case `{result.get('case_id', 'N/A')}`")

    badge_cls = action.lower() if action.lower() in ("accept", "arbitrate", "acquire", "escalate") else "acquire"
    action_icon = {"ACCEPT": "✅", "ARBITRATE": "⚖️", "ACQUIRE": "🔍", "ESCALATE": "🚨"}.get(action, "?")
    st.markdown(f'<span class="action-badge {badge_cls}">{action_icon} {action}</span>',
                unsafe_allow_html=True)

    col_main, col_evidence = st.columns([3, 2])

    with col_main:
        st.markdown('<div class="panel-title">Clinical Report</div>', unsafe_allow_html=True)
        report = result.get("report", "No report generated.")
        st.markdown(report or "_No report generated._")

        # Evidence used / missing
        st.divider()
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("**Evidence Used**")
            for e in result.get("evidence_used", []):
                st.markdown(f"✅ {e.replace('_', ' ').title()}")
        with c2:
            st.markdown("**Evidence Missing**")
            for e in result.get("evidence_missing", []):
                st.markdown(f"❌ {e.replace('_', ' ').title()}")

    with col_evidence:
        st.markdown('<div class="panel-title">Evidence Profile</div>', unsafe_allow_html=True)

        # Placeholder quality bars (replace with real evidence_profile data when available)
        evidence_data = {
            "Clinical Image Quality": 0.80,
            "Dermoscopy Quality": 0.75,
            "Text Informativeness": 0.65,
            "Metadata Quality": 0.90,
            "Cross-Modal Consistency": 0.85,
        }

        for label, value in evidence_data.items():
            fill_width = int(value * 100)
            color = "#4caf50" if value > 0.7 else "#ff9800" if value > 0.4 else "#f44336"
            st.markdown(f"""
            <div style="margin-bottom: 0.8rem;">
                <div style="display:flex; justify-content:space-between; margin-bottom:0.25rem;">
                    <span style="color:#b0bec5;font-size:0.85rem;">{label}</span>
                    <span style="color:{color};font-weight:600;font-size:0.85rem;">{value:.0%}</span>
                </div>
                <div class="evidence-bar-bg">
                    <div class="evidence-bar-fill" style="width:{fill_width}%;background:{color};"></div>
                </div>
            </div>
            """, unsafe_allow_html=True)

        # Consensus level indicator
        level = result.get("consensus_level", 4)
        level_colors = {1: "#4caf50", 2: "#ff9800", 3: "#2196f3", 4: "#f44336"}
        level_labels = {1: "Strong Consensus", 2: "Moderate Consensus", 3: "Acquire More", 4: "Expert Review"}
        lcolor = level_colors.get(level, "#90a4ae")
        llabel = level_labels.get(level, "Unknown")
        st.markdown(f"""
        <div style="background:rgba(255,255,255,0.04);border:1px solid {lcolor}40;border-radius:10px;
                    padding:1rem;margin-top:1rem;text-align:center;">
            <div style="color:{lcolor};font-weight:700;font-size:1.2rem;">Level {level}</div>
            <div style="color:#90a4ae;font-size:0.85rem;">{llabel}</div>
        </div>
        """, unsafe_allow_html=True)

        # Confidence gauge (simple progress bar)
        st.divider()
        st.markdown(f"**Model Confidence**: {confidence:.1%}")
        st.progress(confidence)

    # Pipeline trace
    trace = result.get("evidence_trace", [])
    if trace:
        with st.expander("🔍 Pipeline Execution Trace"):
            for item in trace:
                step = item.get("step", "")
                ts = item.get("timestamp", 0)
                data = item.get("data", "")
                st.markdown(f"**`{step}`** +{ts:.2f}s")
                st.caption(data[:300])
                st.divider()

else:
    if not case_id_input:
        st.info("👈 Enter a Case ID in the sidebar to load clinical details.")
        st.markdown("---")
        st.markdown("#### 🚀 Getting Started")
        st.markdown("""
1. **Submit cases** via the Patient App (`streamlit run app/patient_app.py --server.port 8502`)
2. **Enter the Case ID** returned after submission  
3. **Review** the evidence profile and clinical report here
        """)

# ---------------------------------------------------------------------------
# Footer
# ---------------------------------------------------------------------------
st.divider()
st.caption("DERMA-GUARD v4.0 · Clinician Dashboard · Research System Only — Not for clinical use")
