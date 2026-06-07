"""HouseSignal AI Streamlit home page."""

from __future__ import annotations

import streamlit as st

from src.security.secrets import get_secret_status

try:
    from streamlit_extras.metric_cards import style_metric_cards
except ImportError:  # pragma: no cover - optional UI dependency fallback.
    style_metric_cards = None

st.set_page_config(page_title="HouseSignal AI", page_icon="HS", layout="wide")

st.markdown(
    """
    <style>
    .stApp { background: linear-gradient(135deg, #f7fbf8 0%, #eef6f2 45%, #f7f5ee 100%); }
    .hero-card { padding: 2rem; border-radius: 24px; background: #ffffffcc; border: 1px solid #d8e5df; box-shadow: 0 18px 45px rgba(31, 66, 52, 0.08); }
    .metric-card { padding: 1rem; border-radius: 18px; background: white; border: 1px solid #dce8e2; }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="hero-card">
      <h1>HouseSignal AI</h1>
      <p>Multi-agent commercial real estate diligence, underwriting, market intelligence, and recommendation workflow.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

st.write("")

c1, c2, c3, c4 = st.columns(4)
with c1:
    st.metric("Document Agents", "5")
with c2:
    st.metric("Core Analysis Agents", "4")
with c3:
    st.metric("RentCast Mode", "Cache-first")
with c4:
    st.metric("Secrets", "Env only")

if style_metric_cards:
    style_metric_cards(background_color="#ffffff", border_left_color="#0f766e", border_color="#d8e5df")

st.subheader("Workflow")
st.write(
    "Upload lease agreements, rent rolls, offering memorandums, T12s, and property condition reports. "
    "HouseSignal AI retrieves relevant evidence, routes it to specialized agents, and combines the output into financial, risk, market, and recommendation views."
)

st.subheader("Configuration Status")
for item in get_secret_status():
    st.write(f"- {item.label}: {'configured' if item.configured else 'not configured'}")

st.info("Secret values are never shown here. This page only reports whether required environment variables exist.")
