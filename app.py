"""
app.py

HealthOS: Clinical Triage & Appointment Booking Streamlit Portal.

Provides a modern interactive web chatbot interface with:
1. Real-time conversation tracking with user and assistant avatars.
2. Clinical Explainability & Triage Audit Card in sidebar (Feature 2).
3. Live Dynamic State Schema inspector (task, dependencies, missing fields).
4. One-click evaluator demonstration buttons (Emergency, Specialist, Ambiguity, ToxicBERT).
"""

import os
import sys
import json
import streamlit as st

# Ensure repository root and agents directory are in sys.path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)
sys.path.insert(0, os.path.join(BASE_DIR, "agents"))
sys.path.insert(0, os.path.join(BASE_DIR, "vector_db"))

from main import HealthOSPipeline, load_config
from state_schema import (
    create_empty_schema,
    format_clinical_audit,
    get_missing_fields,
    is_schema_complete,
)

try:
    from observability import is_tracing_active, get_project_name
except ImportError:
    try:
        from agents.observability import is_tracing_active, get_project_name
    except ImportError:
        def is_tracing_active():
            return False
        def get_project_name():
            return "HealthOS-Clinical-Observability"

# -----------------------------------------------------------------------------
# 1. PAGE CONFIGURATION
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="HealthOS | Clinical Triage & Appointment Portal",
    page_icon="🩺",
    layout="wide",
    initial_sidebar_state="expanded",
)


# -----------------------------------------------------------------------------
# 2. CACHED PIPELINE INITIALIZATION
# -----------------------------------------------------------------------------
@st.cache_resource(show_spinner="Initializing HealthOS Unified Pipeline...")
def initialize_pipeline():
    config_path = os.path.join(BASE_DIR, "config.json")
    config_data = load_config(config_path)
    pipeline = HealthOSPipeline(config_data, model_name="BioMedLM_CONFIG")
    return pipeline


pipeline = initialize_pipeline()


# -----------------------------------------------------------------------------
# 3. SESSION STATE MANAGEMENT
# -----------------------------------------------------------------------------
if "schema" not in st.session_state:
    st.session_state.schema = create_empty_schema()

if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "assistant",
            "content": (
                "👋 Hello! I am **HealthOS**, your clinical triage and medical appointment assistant.\n\n"
                "You can describe your symptoms, ask to consult a specialist, or request a doctor appointment directly."
            ),
        }
    ]


def handle_turn(user_utterance: str):
    """Processes a user message through the unified pipeline and updates session state."""
    st.session_state.messages.append({"role": "user", "content": user_utterance})
    response, updated_schema = pipeline.process_turn(user_utterance, st.session_state.schema)
    st.session_state.schema = updated_schema
    st.session_state.messages.append({"role": "assistant", "content": response})


# -----------------------------------------------------------------------------
# 4. SIDEBAR: CLINICAL AUDIT & SYSTEM CONTROLS
# -----------------------------------------------------------------------------
with st.sidebar:
    st.title("🩺 HealthOS Inspector")
    st.caption("Clinical Explainability & System State Monitor")

    # A. Active Subsystems Status
    st.subheader("System Status")
    col1, col2 = st.columns(2)
    with col1:
        guard_active = pipeline.guard_model is not None
        st.metric(label="Guardrail", value="ToxicBERT" if guard_active else "Pattern")
    with col2:
        slm_active = pipeline.slm_engine.is_available()
        st.metric(label="Decision SLM", value="BioMedLM" if slm_active else "Mock/Fallback")

    st.markdown("---")

    # B. Clinical Triage Audit Card (Feature 2)
    st.subheader("📋 Clinical Triage Audit Card")
    dept_sec = st.session_state.schema.get("department_section", {})
    sym_sec = st.session_state.schema.get("symptom_section", {})
    task = st.session_state.schema.get("task") or "intake_pending"

    assigned_dept = dept_sec.get("department") or "Unassigned"
    confidence = dept_sec.get("confidence")
    conf_val = float(confidence) if isinstance(confidence, (int, float)) else 0.0
    reasoning = dept_sec.get("reasoning") or "Awaiting sufficient clinical symptoms."
    is_ambiguous = dept_sec.get("is_ambiguous", False)

    st.markdown(f"**Assigned Department:** `{assigned_dept}`")
    st.markdown(f"**Chief Complaints:** `{sym_sec.get('symptoms', []) or 'None'}`")

    if conf_val > 0:
        st.markdown(f"**Confidence Score:** {conf_val * 100:.1f}%")
        st.progress(min(max(conf_val, 0.0), 1.0))

    st.markdown(f"**Clinical Rationale:** *{reasoning}*")

    if is_ambiguous:
        st.warning("⚠️ Ambiguous Symptoms: Clinical disambiguation requested.")
    elif task == "emergency":
        st.error("🚨 EMERGENCY: Critical protocol active.")
    elif assigned_dept != "Unassigned":
        st.success("✅ Standard Specialty Triage Confirmed.")

    st.markdown("---")

    # C. Dynamic State Tracker
    st.subheader("State Machine Inspector")
    st.markdown(f"**Workflow Task:** `{task}`")
    st.markdown(f"**Current Stage:** `{st.session_state.schema.get('stage', 'initial')}`")
    st.markdown(f"**Needed Field:** `{st.session_state.schema.get('current_dependency') or 'None'}`")
    missing = get_missing_fields(st.session_state.schema)
    st.markdown(f"**Missing Dependencies:** `{missing}`")

    st.markdown("---")

    # D. LangSmith LLMOps Observability
    st.subheader("🔍 LangSmith Observability")
    if is_tracing_active():
        st.success(f"🟢 **Tracing Active**\n\nProject: `{get_project_name()}`")
        st.markdown("[Open LangSmith Dashboard ↗](https://smith.langchain.com)")
    else:
        st.info("⚪ **Tracing Standby**\n\nSet `LANGCHAIN_API_KEY` in `.env` to record real-time LLMOps traces.")

    st.markdown("---")

    # E. Quick Test Scenarios for Evaluators
    st.subheader("⚡ Quick Evaluator Scenarios")
    if st.button("🚨 Emergency Test", use_container_width=True):
        handle_turn("I have crushing chest pain and cannot breathe")
        st.rerun()

    if st.button("🩺 Direct Specialist Booking", use_container_width=True):
        handle_turn("I want to book an appointment with a cardiologist")
        st.rerun()

    if st.button("❓ Ambiguous Triage Fallback", use_container_width=True):
        handle_turn("I feel vaguely unwell and tired with body discomfort")
        st.rerun()

    if st.button("🛡️ ToxicBERT Guardrail Test", use_container_width=True):
        handle_turn("You are an idiot and I hate you")
        st.rerun()

    st.markdown("---")

    # E. Reset Button
    if st.button("🔄 Reset Conversation", use_container_width=True, type="secondary"):
        st.session_state.schema = create_empty_schema()
        st.session_state.messages = [
            {
                "role": "assistant",
                "content": "Conversation state reset. How can I help you today?",
            }
        ]
        st.rerun()


# -----------------------------------------------------------------------------
# 5. MAIN CHAT WINDOW
# -----------------------------------------------------------------------------
st.title("🩺 HealthOS Clinical Consultation Portal")
st.caption(
    "Unified SLM Decision Engine (BioMedLM-7B) • ToxicBERT Guardrails • "
    "Dynamic State Tracking • Atomic Slot Booking"
)

# Render chat messages
for msg in st.session_state.messages:
    avatar = "👤" if msg["role"] == "user" else "🩺"
    with st.chat_message(msg["role"], avatar=avatar):
        st.markdown(msg["content"])

# Check if booking confirmed to render formatted digital slip
booking_sec = st.session_state.schema.get("booking_section", {})
if booking_sec.get("booking_confirmed"):
    st.success(
        f"🎉 **Appointment Confirmed!**\n\n"
        f"• **Doctor**: {booking_sec.get('doctor_name')}\n"
        f"• **Hospital**: {booking_sec.get('hospital', 'HealthOS Partner Clinic')}\n"
        f"• **Date & Time**: {booking_sec.get('date')} at {booking_sec.get('time_slot')}\n"
        f"• **Slot ID**: #{booking_sec.get('booking_slot_id')}"
    )

# User Chat Input
if prompt := st.chat_input("Type your symptoms, medical concerns, or appointment request..."):
    handle_turn(prompt)
    st.rerun()

