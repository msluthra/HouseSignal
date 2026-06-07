"""Commercial deal underwriting page."""

from __future__ import annotations

import plotly.graph_objects as go
import streamlit as st

from src.agents.base import AgentContext
from src.agents.financial_analysis_agent import FinancialAnalysisAgent
from src.agents.recommendation_agent import RecommendationAgent
from src.agents.risk_analysis_agent import RiskAnalysisAgent

st.set_page_config(page_title="Deal Underwriting", layout="wide")
st.title("Deal Underwriting")
st.caption("First-pass commercial real estate underwriting with financial, risk, and recommendation agents.")

left, right = st.columns([1, 1])
with left:
    st.subheader("Inputs")
    purchase_price = st.number_input("Purchase Price", min_value=0.0, value=5_000_000.0, step=50_000.0)
    annual_gross_income = st.number_input("Annual Gross Income", min_value=0.0, value=520_000.0, step=10_000.0)
    annual_operating_expenses = st.number_input("Annual Operating Expenses", min_value=0.0, value=210_000.0, step=5_000.0)
    annual_debt_service = st.number_input("Annual Debt Service", min_value=0.0, value=240_000.0, step=5_000.0)
    equity_invested = st.number_input("Equity Invested", min_value=0.0, value=1_500_000.0, step=25_000.0)
    vacancy_rate = st.slider("Vacancy Rate", 0.0, 0.5, 0.06, 0.01)
    capex_reserve = st.number_input("Immediate Capex Reserve", min_value=0.0, value=150_000.0, step=10_000.0)

property_profile = {
    "purchase_price": purchase_price,
    "annual_gross_income": annual_gross_income,
    "annual_operating_expenses": annual_operating_expenses,
    "annual_debt_service": annual_debt_service,
    "equity_invested": equity_invested,
    "vacancy_rate": vacancy_rate,
    "capex_reserve": capex_reserve,
    "market_signal_score": 58.0,
}

financial_result = FinancialAnalysisAgent().run(AgentContext(property_profile=property_profile))
property_profile.update(financial_result.metrics)
risk_result = RiskAnalysisAgent().run(AgentContext(property_profile=property_profile))
property_profile.update(risk_result.metrics)
recommendation_result = RecommendationAgent().run(AgentContext(property_profile=property_profile))

with right:
    st.subheader("Agent Output")
    st.metric("Recommendation", str(recommendation_result.metrics.get("recommendation_label", "hold/monitor")))
    st.metric("Investment Score", f"{float(recommendation_result.metrics.get('investment_score', 0.0)):.1f}/100")
    st.metric("Risk Score", f"{float(risk_result.metrics.get('risk_score', 0.0)):.1f}/100")

fig = go.Figure(
    data=[
        go.Bar(
            x=["Cap Rate", "DSCR", "Cash-on-Cash"],
            y=[
                float(financial_result.metrics.get("cap_rate", 0.0)) * 100,
                float(financial_result.metrics.get("dscr", 0.0)),
                float(financial_result.metrics.get("cash_on_cash", 0.0)) * 100,
            ],
            marker_color=["#0f766e", "#2563eb", "#ca8a04"],
        )
    ]
)
fig.update_layout(height=360, margin=dict(l=20, r=20, t=40, b=20))
st.plotly_chart(fig, use_container_width=True)

for result in [financial_result, risk_result, recommendation_result]:
    with st.expander(result.agent_name.replace("_", " ").title(), expanded=True):
        st.write(result.summary)
        for finding in result.findings:
            st.write(f"- {finding}")
        for risk in result.risks:
            st.warning(risk)
