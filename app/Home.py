"""HouseSignal AI Streamlit command center."""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import pandas as pd
import streamlit as st

from app.ui import apply_theme, hero, status_step
from src.agents.base import AgentContext
from src.agents.financial_analysis_agent import FinancialAnalysisAgent
from src.agents.market_data_agent import MarketDataAgent
from src.agents.recommendation_agent import RecommendationAgent
from src.agents.risk_analysis_agent import RiskAnalysisAgent
from src.mock.sample_data import AGENT_PIPELINE, MARKET_SNAPSHOTS, SAMPLE_DEAL
from src.security.secrets import get_secret_status
from src.services.supabase.config import get_supabase_runtime_config

try:
    import plotly.graph_objects as go
except ImportError:  # pragma: no cover - optional chart dependency fallback.
    go = None

try:
    from streamlit_extras.metric_cards import style_metric_cards
except ImportError:  # pragma: no cover - optional UI dependency fallback.
    style_metric_cards = None

st.set_page_config(page_title="HouseSignal AI", page_icon="HS", layout="wide")
apply_theme()

hero(
    "HouseSignal AI",
    "A mock-data commercial real estate command center for document intelligence, underwriting, market context, API governance, and investment recommendations.",
    pills=["Mock data only", "Multi-agent workflow", "RAG-ready", "Cache-first APIs"],
)

profile = SAMPLE_DEAL.to_agent_profile()
financial = FinancialAnalysisAgent().run(AgentContext(property_profile=profile))
profile.update(financial.metrics)
risk = RiskAnalysisAgent().run(AgentContext(property_profile=profile))
profile.update(risk.metrics)
recommendation = RecommendationAgent().run(AgentContext(property_profile=profile))
market = MarketDataAgent().run(
    AgentContext(
        property_profile=profile,
        market_snapshot=next(item for item in MARKET_SNAPSHOTS if item["city"] == SAMPLE_DEAL.city),
    )
)

score = float(recommendation.metrics.get("investment_score", 0.0))
risk_score = float(risk.metrics.get("risk_score", 0.0))
cap_rate = float(financial.metrics.get("cap_rate", 0.0))
dscr = float(financial.metrics.get("dscr", 0.0))

st.subheader("Sample Deal Snapshot")
st.caption("All numbers on this dashboard are demo values so the workflow can be tested before real files/API keys are connected.")

m1, m2, m3, m4, m5 = st.columns(5)
m1.metric("Deal", SAMPLE_DEAL.name)
m2.metric("Units", f"{SAMPLE_DEAL.units}")
m3.metric("Recommendation", str(recommendation.metrics.get("recommendation_label", "hold/monitor")).title())
m4.metric("Investment Score", f"{score:.1f}/100")
m5.metric("Risk Score", f"{risk_score:.1f}/100")

if style_metric_cards:
    style_metric_cards(background_color="#ffffff", border_left_color="#0f766e", border_color="#d8e5df")

left, right = st.columns([1.2, 1])
with left:
    st.markdown("### Agent Workflow")
    for step in AGENT_PIPELINE:
        status_step(step["step"], step["status"], step["detail"])

with right:
    st.markdown("### Underwriting Pulse")
    if go:
        fig = go.Figure(
            go.Indicator(
                mode="gauge+number",
                value=score,
                title={"text": "Investment Score"},
                gauge={
                    "axis": {"range": [0, 100]},
                    "bar": {"color": "#0f766e"},
                    "steps": [
                        {"range": [0, 45], "color": "#f8d7ca"},
                        {"range": [45, 70], "color": "#f7e7b5"},
                        {"range": [70, 100], "color": "#caeadc"},
                    ],
                },
            )
        )
        fig.update_layout(height=260, margin=dict(l=20, r=20, t=40, b=20), paper_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.progress(score / 100, text=f"Investment Score: {score:.1f}/100")

    st.write(f"**Cap rate:** {cap_rate * 100:.2f}%")
    st.write(f"**DSCR:** {dscr:.2f}x")
    st.write(f"**Market agent:** {market.summary}")

st.markdown("### Pilot Market Context")
market_df = pd.DataFrame(MARKET_SNAPSHOTS)
if go:
    chart = go.Figure()
    chart.add_trace(go.Bar(x=market_df["city"], y=market_df["market_signal"], name="Market Signal", marker_color="#0f766e"))
    chart.add_trace(go.Bar(x=market_df["city"], y=market_df["risk"], name="Risk", marker_color="#b45309"))
    chart.update_layout(barmode="group", height=330, margin=dict(l=20, r=20, t=35, b=20), paper_bgcolor="rgba(0,0,0,0)")
    st.plotly_chart(chart, use_container_width=True)
else:
    st.bar_chart(market_df.set_index("city")[["market_signal", "risk"]])

st.markdown("### Secure Configuration Status")
st.caption("Only generic service status is shown. Secret names and secret values are not rendered in the UI.")
config_cols = st.columns(4)
for idx, item in enumerate(get_secret_status()):
    with config_cols[idx % 4]:
        st.metric(item.label, "Configured" if item.configured else "Not configured")

runtime = get_supabase_runtime_config()
st.metric("Supabase Runtime", runtime.mode.value.title(), help="Mock mode keeps localhost working without real Supabase credentials.")

st.info("Next: use the sidebar pages to test underwriting, document RAG, map exploration, and API usage controls with mock data.")
