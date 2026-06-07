"""Risk analysis agent for CRE deals."""

from __future__ import annotations

from src.agents.base import AgentContext, AgentResult


class RiskAnalysisAgent:
    """Estimate deal risk from market, document, financing, and data quality signals."""

    name = "risk_analysis_agent"

    def run(self, context: AgentContext) -> AgentResult:
        """Return a simple auditable risk score."""
        p = context.property_profile
        vacancy = float(p.get("vacancy_rate", 0.0) or 0.0)
        dscr = float(p.get("dscr", 0.0) or 0.0)
        capex_reserve = float(p.get("capex_reserve", 0.0) or 0.0)
        purchase_price = float(p.get("purchase_price", 0.0) or 0.0)

        score = 35.0
        score += min(vacancy * 100, 25)
        if dscr and dscr < 1.2:
            score += 20
        if purchase_price and capex_reserve / purchase_price > 0.05:
            score += 15
        if not context.retrieved_chunks:
            score += 10
        score = max(0.0, min(score, 100.0))

        risks = []
        if vacancy > 0.08:
            risks.append("Vacancy is elevated versus a stabilized assumption.")
        if dscr and dscr < 1.2:
            risks.append("Financing risk is elevated because DSCR is below 1.20x.")
        if not context.retrieved_chunks:
            risks.append("Document evidence is missing, so diligence risk remains high.")

        return AgentResult(
            agent_name=self.name,
            summary="Estimated downside risk from underwriting and diligence signals.",
            findings=[f"Risk score: {score:.1f}/100"],
            risks=risks,
            metrics={"risk_score": score},
            confidence=0.6,
        )
