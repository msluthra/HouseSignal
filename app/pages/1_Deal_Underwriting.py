"""Commercial deal underwriting page."""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import pandas as pd
import streamlit as st

from app.ui import apply_theme, hero
from src.agents.base import AgentContext
from src.agents.financial_analysis_agent import FinancialAnalysisAgent
from src.agents.recommendation_agent import RecommendationAgent
from src.agents.risk_analysis_agent import RiskAnalysisAgent
from src.mock.sample_data import SAMPLE_DEAL

try:
    import plotly.graph_objects as go
except ImportError:  # pragma: no cover - optional chart dependency fallback.
    go = None

st.set_page_config(page_title="HouseSignal AI | Underwriting", layout="wide")
apply_theme()
hero(
    "Deal Underwriting",
    "Stress-test a sample multifamily acquisition and watch the financial, risk, and recommendation agents update from the same assumptions.",
    pills=["Financial agent", "Risk agent", "Recommendation agent", "Mock numbers"],
)

with st.sidebar:
    st.header("Sample Deal")
    st.write(SAMPLE_DEAL.name)
    st.caption(f"{SAMPLE_DEAL.asset_type} · {SAMPLE_DEAL.city}, {SAMPLE_DEAL.state}")
    scenario = st.radio("Scenario", ["Base Case", "Conservative", "Upside"], horizontal=False)

scenario_mods = {
    "Base Case": {"income": 1.0, "expenses": 1.0, "vacancy": SAMPLE_DEAL.vacancy_rate, "capex": SAMPLE_DEAL.capex_reserve},
    "Conservative": {"income": 0.96, "expenses": 1.07, "vacancy": 0.095, "capex": SAMPLE_DEAL.capex_reserve * 1.25},
    "Upside": {"income": 1.06, "expenses": 0.98, "vacancy": 0.045, "capex": SAMPLE_DEAL.capex_reserve * 0.85},
}
mods = scenario_mods[scenario]

left, right = st.columns([1, 1.25])
with left:
    st.subheader("Deal Inputs")
    purchase_price = st.number_input("Purchase Price", min_value=0.0, value=float(SAMPLE_DEAL.purchase_price), step=50_000.0)
    annual_gross_income = st.number_input(
        "Annual Gross Income",
        min_value=0.0,
        value=float(SAMPLE_DEAL.annual_gross_income * mods["income"]),
        step=10_000.0,
    )
    annual_operating_expenses = st.number_input(
        "Annual Operating Expenses",
        min_value=0.0,
        value=float(SAMPLE_DEAL.annual_operating_expenses * mods["expenses"]),
        step=5_000.0,
    )
    annual_debt_service = st.number_input("Annual Debt Service", min_value=0.0, value=float(SAMPLE_DEAL.annual_debt_service), step=5_000.0)
    equity_invested = st.number_input("Equity Invested", min_value=0.0, value=float(SAMPLE_DEAL.equity_invested), step=25_000.0)
    vacancy_rate = st.slider("Vacancy Rate", 0.0, 0.5, float(mods["vacancy"]), 0.005)
    capex_reserve = st.number_input("Immediate Capex Reserve", min_value=0.0, value=float(mods["capex"]), step=10_000.0)

property_profile = {
    "name": SAMPLE_DEAL.name,
    "address": SAMPLE_DEAL.address,
    "city": SAMPLE_DEAL.city,
    "asset_type": SAMPLE_DEAL.asset_type,
    "units": SAMPLE_DEAL.units,
    "purchase_price": purchase_price,
    "annual_gross_income": annual_gross_income,
    "annual_operating_expenses": annual_operating_expenses,
    "annual_debt_service": annual_debt_service,
    "equity_invested": equity_invested,
    "vacancy_rate": vacancy_rate,
    "capex_reserve": capex_reserve,
    "market_signal_score": SAMPLE_DEAL.market_signal_score,
}

financial_result = FinancialAnalysisAgent().run(AgentContext(property_profile=property_profile))
property_profile.update(financial_result.metrics)
risk_result = RiskAnalysisAgent().run(AgentContext(property_profile=property_profile))
property_profile.update(risk_result.metrics)
recommendation_result = RecommendationAgent().run(AgentContext(property_profile=property_profile))

noi = float(financial_result.metrics.get("noi", 0.0))
cap_rate = float(financial_result.metrics.get("cap_rate", 0.0))
dscr = float(financial_result.metrics.get("dscr", 0.0))
cash_on_cash = float(financial_result.metrics.get("cash_on_cash", 0.0))
risk_score = float(risk_result.metrics.get("risk_score", 0.0))
investment_score = float(recommendation_result.metrics.get("investment_score", 0.0))

with right:
    st.subheader("Agent Output")
    k1, k2, k3 = st.columns(3)
    k1.metric("Recommendation", str(recommendation_result.metrics.get("recommendation_label", "hold/monitor")).title())
    k2.metric("Investment Score", f"{investment_score:.1f}/100")
    k3.metric("Risk Score", f"{risk_score:.1f}/100")

    k4, k5, k6, k7 = st.columns(4)
    k4.metric("NOI", f"${noi:,.0f}")
    k5.metric("Cap Rate", f"{cap_rate * 100:.2f}%")
    k6.metric("DSCR", f"{dscr:.2f}x")
    k7.metric("Cash-on-Cash", f"{cash_on_cash * 100:.2f}%")

    chart_data = pd.DataFrame(
        {
            "metric": ["Cap Rate", "DSCR", "Cash-on-Cash", "Risk Score"],
            "value": [cap_rate * 100, dscr, cash_on_cash * 100, risk_score],
        }
    )
    if go:
        fig = go.Figure(
            data=[
                go.Bar(
                    x=chart_data["metric"],
                    y=chart_data["value"],
                    marker_color=["#0f766e", "#2563eb", "#ca8a04", "#b45309"],
                )
            ]
        )
        fig.update_layout(height=340, margin=dict(l=20, r=20, t=35, b=20), paper_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.bar_chart(chart_data.set_index("metric"))

st.subheader("Sensitivity Table")
sensitivity_rows = []
for vacancy in [0.04, 0.06, 0.08, 0.10, 0.12]:
    effective_income = annual_gross_income * (1 - vacancy)
    scenario_noi = effective_income - annual_operating_expenses
    sensitivity_rows.append(
        {
            "Vacancy": f"{vacancy * 100:.0f}%",
            "Effective Income": effective_income,
            "NOI": scenario_noi,
            "Cap Rate": scenario_noi / purchase_price if purchase_price else 0.0,
            "DSCR": scenario_noi / annual_debt_service if annual_debt_service else 0.0,
        }
    )
sensitivity = pd.DataFrame(sensitivity_rows)
st.dataframe(
    sensitivity.style.format({"Effective Income": "${:,.0f}", "NOI": "${:,.0f}", "Cap Rate": "{:.2%}", "DSCR": "{:.2f}x"}),
    use_container_width=True,
)

for result in [financial_result, risk_result, recommendation_result]:
    with st.expander(result.agent_name.replace("_", " ").title(), expanded=True):
        st.write(result.summary)
        for finding in result.findings:
            st.write(f"- {finding}")
        for risk in result.risks:
            st.warning(risk)
