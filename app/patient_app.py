"""
app/patient_app.py — Streamlit Patient App for DERMA-GUARD v4.0

Sections:
  1. Upload Form   — drag-and-drop images + text + metadata
  2. Status View   — track case evidence timeline
  3. Results View  — final report with confidence indicator
"""
import io
import json
import time
from typing import Optional

import requests
import streamlit as st
from PIL import Image

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
API_BASE = "http://localhost:8000"

st.set_page_config(
    page_title="DERMA-GUARD v4.0 — Patient Portal",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# Styles
# ---------------------------------------------------------------------------
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }
    
    .main { background: #0f0f1a; }
    
    .hero-card {
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
        border: 1px solid rgba(100, 149, 237, 0.3);
        border-radius: 16px;
        padding: 2rem;
        margin-bottom: 2rem;
        text-align: center;
    }
    
    .hero-title {
        font-size: 2.5rem;
        font-weight: 700;
        background: linear-gradient(135deg, #64b5f6, #81d4fa, #b3e5fc);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.5rem;
    }
    
    .hero-subtitle {
        color: #90a4ae;
        font-size: 1rem;
    }
    
    .action-badge {
        display: inline-block;
        padding: 0.4rem 1.2rem;
        border-radius: 999px;
        font-weight: 600;
        font-size: 0.9rem;
        letter-spacing: 0.05em;
    }
    
    .badge-accept   { background: rgba(76, 175, 80, 0.2); color: #81c784; border: 1px solid #4caf50; }
    .badge-arbitrate { background: rgba(255, 193, 7, 0.2); color: #ffd54f; border: 1px solid #ffc107; }
    .badge-acquire  { background: rgba(33, 150, 243, 0.2); color: #64b5f6; border: 1px solid #2196f3; }
    .badge-escalate { background: rgba(244, 67, 54, 0.2); color: #ef9a9a; border: 1px solid #f44336; }
    
    .evidence-card {
        background: rgba(255,255,255,0.04);
        border: 1px solid rgba(255,255,255,0.08);
        border-radius: 12px;
        padding: 1.5rem;
        margin-bottom: 1rem;
    }
    
    .timeline-item {
        border-left: 2px solid #2196f3;
        padding-left: 1rem;
        margin-bottom: 1rem;
    }
    
    .disclaimer {
        background: rgba(244, 67, 54, 0.1);
        border: 1px solid rgba(244, 67, 54, 0.3);
        border-radius: 8px;
        padding: 1rem;
        color: #ef9a9a;
        font-size: 0.85rem;
        margin-top: 2rem;
    }
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Session state
# ---------------------------------------------------------------------------
if "case_id" not in st.session_state:
    st.session_state.case_id = None
if "result" not in st.session_state:
    st.session_state.result = None
if "page" not in st.session_state:
    st.session_state.page = "upload"

# ---------------------------------------------------------------------------
# Sidebar navigation
# ---------------------------------------------------------------------------
with st.sidebar:
    st.markdown("## 🔬 DERMA-GUARD")
    st.markdown("**v4.0** · Research System")
    st.divider()
    page = st.radio(
        "Navigate",
        ["📤 Upload Case", "📊 Case Status", "📋 Results"],
        key="nav",
        index=0,
    )
    st.divider()
    # API status
    try:
        resp = requests.get(f"{API_BASE}/health", timeout=3)
        if resp.status_code == 200:
            h = resp.json()
            st.success("✅ API Connected")
            st.caption(f"GPU: {'✓' if h.get('gpu_available') else '✗'}")
            st.caption(f"LLM: {'✓' if h.get('ollama_available') else '✗'}")
        else:
            st.error("⚠ API Error")
    except Exception:
        st.warning("🔴 API Offline\nStart: `python src/main.py`")

# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------

def action_badge_html(action: str) -> str:
    cls = {
        "ACCEPT": "badge-accept",
        "ARBITRATE": "badge-arbitrate",
        "ACQUIRE": "badge-acquire",
        "ESCALATE": "badge-escalate",
        "ABSTAIN": "badge-escalate",
    }.get(action, "badge-acquire")
    icon = {"ACCEPT": "✅", "ARBITRATE": "⚖️", "ACQUIRE": "🔍",
            "ESCALATE": "🚨", "ABSTAIN": "⏸️"}.get(action, "❓")
    return f'<span class="action-badge {cls}">{icon} {action}</span>'


def confidence_color(conf: float) -> str:
    if conf >= 0.8:
        return "#81c784"
    elif conf >= 0.5:
        return "#ffd54f"
    return "#ef9a9a"


# ---------------------------------------------------------------------------
# Page: Upload
# ---------------------------------------------------------------------------
if "Upload" in page:
    st.markdown("""
    <div class="hero-card">
        <div class="hero-title">🔬 DERMA-GUARD</div>
        <div class="hero-subtitle">Agentic Evidence-Management Framework for Dermatological Diagnosis</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("### 📤 Submit Your Case")
    st.markdown(
        "> Upload your skin lesion images and describe your symptoms. "
        "The system will analyse all available evidence."
    )

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("#### Clinical Photo")
        clinical_file = st.file_uploader(
            "Upload clinical photograph",
            type=["jpg", "jpeg", "png"],
            key="clinical_upload",
            help="Standard photograph of the skin lesion",
        )
        if clinical_file:
            st.image(Image.open(clinical_file), caption="Clinical image preview", use_column_width=True)
            clinical_file.seek(0)

    with col2:
        st.markdown("#### Dermoscopy Image")
        dermo_file = st.file_uploader(
            "Upload dermoscopy image (optional)",
            type=["jpg", "jpeg", "png"],
            key="dermo_upload",
            help="Dermoscopy image if available",
        )
        if dermo_file:
            st.image(Image.open(dermo_file), caption="Dermoscopy preview", use_column_width=True)
            dermo_file.seek(0)

    st.markdown("#### Patient Description")
    patient_text = st.text_area(
        "Describe your symptoms",
        placeholder=(
            "Example: I noticed this mole about 3 months ago. "
            "It has been growing slowly and sometimes itches. "
            "The border looks irregular to me."
        ),
        height=120,
        key="patient_text",
    )

    st.markdown("""
    <div class="disclaimer">
        ⚠️ <strong>Research System Only</strong>: DERMA-GUARD is a research prototype and 
        has NOT been clinically validated. Results should NOT be used for medical diagnosis. 
        Always consult a qualified dermatologist.
    </div>
    """, unsafe_allow_html=True)

    st.divider()
    col_btn, col_info = st.columns([1, 3])
    with col_btn:
        submit = st.button("🚀 Analyse Case", type="primary", use_container_width=True)

    if submit:
        if not clinical_file and not dermo_file and not patient_text:
            st.error("Please provide at least one input (image or description).")
        else:
            with st.spinner("🔬 Running multimodal analysis…"):
                try:
                    files = {}
                    if clinical_file:
                        files["clinical_image"] = (clinical_file.name, clinical_file.read(), "image/jpeg")
                    if dermo_file:
                        files["dermoscopy_image"] = (dermo_file.name, dermo_file.read(), "image/jpeg")
                    data = {}
                    if patient_text:
                        data["patient_text"] = patient_text

                    resp = requests.post(f"{API_BASE}/predict", files=files, data=data, timeout=120)

                    if resp.status_code == 200:
                        result = resp.json()
                        st.session_state.result = result
                        st.session_state.case_id = result.get("case_id")
                        st.success(f"✅ Analysis complete! Case ID: **{st.session_state.case_id}**")
                        st.info("👉 Navigate to **Results** to see your report.")
                    else:
                        st.error(f"API error {resp.status_code}: {resp.text[:200]}")
                except requests.exceptions.ConnectionError:
                    st.error("Cannot connect to API. Start the server: `python src/main.py`")
                except Exception as e:
                    st.error(f"Error: {e}")

# ---------------------------------------------------------------------------
# Page: Status
# ---------------------------------------------------------------------------
elif "Status" in page:
    st.markdown("### 📊 Case Status")

    case_id_input = st.text_input(
        "Enter Case ID",
        value=st.session_state.case_id or "",
        placeholder="e.g. a1b2c3d4",
    )

    if st.button("🔍 Fetch Status") and case_id_input:
        try:
            resp = requests.get(f"{API_BASE}/case/{case_id_input}", timeout=10)
            if resp.status_code == 200:
                result = resp.json()
                st.session_state.result = result
                st.session_state.case_id = case_id_input
            else:
                st.error(f"Case not found: {case_id_input}")
        except Exception as e:
            st.error(f"Error: {e}")

    if st.session_state.result:
        result = st.session_state.result
        action = result.get("action", "?")

        st.markdown("#### Evidence Timeline")
        trace = result.get("evidence_trace", [])
        if trace:
            for item in trace:
                step = item.get("step", "")
                ts = item.get("timestamp", 0)
                data = item.get("data", "")
                st.markdown(f"""
                <div class="timeline-item">
                    <strong>{step}</strong> <span style="color:#666">+{ts:.2f}s</span><br/>
                    <small style="color:#90a4ae">{data[:200]}</small>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("No trace data available.")

# ---------------------------------------------------------------------------
# Page: Results
# ---------------------------------------------------------------------------
elif "Results" in page:
    st.markdown("### 📋 Analysis Results")

    if not st.session_state.result:
        st.info("No results yet. Submit a case first.")
    else:
        result = st.session_state.result
        action = result.get("action", "?")
        confidence = result.get("confidence") or 0.0
        diag = result.get("diagnosis")
        report = result.get("report", "")
        evidence_used = result.get("evidence_used", [])
        evidence_missing = result.get("evidence_missing", [])

        # Header
        col1, col2, col3 = st.columns([2, 1, 1])
        with col1:
            st.markdown(f"**Case ID**: `{result.get('case_id', 'N/A')}`")
            st.markdown(action_badge_html(action), unsafe_allow_html=True)
        with col2:
            if confidence:
                color = confidence_color(confidence)
                st.metric("Confidence", f"{confidence:.1%}")
        with col3:
            level = result.get("consensus_level")
            if level:
                st.metric("Consensus Level", f"Level {level}")

        st.divider()

        # Diagnosis display
        if action in ("ACCEPT", "ARBITRATE") and diag is not None:
            class_names = ["Nevus", "Melanoma", "Basal Cell Carcinoma", "Squamous Cell Carcinoma",
                           "Seborrheic Keratosis", "Dermatofibroma", "Vascular Lesion"]
            diag_name = class_names[diag] if 0 <= diag < len(class_names) else f"Class {diag}"
            st.markdown(f"""
            <div class="evidence-card">
                <h4 style="color:#64b5f6">Predicted Diagnosis</h4>
                <h3 style="color:white">{diag_name}</h3>
                <p style="color:#90a4ae">Confidence: {confidence:.1%} · Consensus Level {level}</p>
            </div>
            """, unsafe_allow_html=True)

        elif action == "ACQUIRE":
            target = result.get("acquire_target", "additional information")
            st.warning(f"🔍 **Additional Information Needed**: {target}")

        elif action in ("ESCALATE", "ABSTAIN"):
            reason = result.get("escalate_reason", "See details below")
            st.error(f"🚨 **Human Expert Review Required**: {reason}")

        # Report
        if report:
            with st.expander("📄 Clinical Report", expanded=True):
                st.markdown(report)

        # Evidence summary
        col_used, col_miss = st.columns(2)
        with col_used:
            st.markdown(f"**Evidence Used** ({len(evidence_used)})")
            for e in evidence_used:
                st.markdown(f"  ✅ {e.replace('_', ' ').title()}")
        with col_miss:
            st.markdown(f"**Evidence Missing** ({len(evidence_missing)})")
            for e in evidence_missing:
                st.markdown(f"  ❌ {e.replace('_', ' ').title()}")

        st.divider()
        st.caption(
            f"⏱ Processing time: {result.get('processing_time_s', 0):.2f}s · "
            "DERMA-GUARD v4.0 · Research Only — Not for clinical use"
        )
