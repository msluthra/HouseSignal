"""Recommendation agent for CRE investment decisions."""

from __future__ import annotations

from src.agents.base import AgentContext, AgentResult


class RecommendationAgent:
    """Combine analysis outputs into a clear recommendation label."""

    name = "recommendation_agent"

    @staticmethod
    def label(score: float) -> str:
        """Map an investment score to a recommendation label."""
        if score >= 75:
            return "strong buy"
        if score >= 60:
            return "buy with caution"
        if score >= 45:
            return "hold/monitor"
        return "avoid"

    def run(self, context: AgentContext) -> AgentResult:
        """Score a deal from provided financial/risk assumptions."""
        p = context.property_profile
        cap_rate = float(p.get("cap_rate", 0.0) or 0.0)
        dscr = float(p.get("dscr", 0.0) or 0.0)
        risk_score = float(p.get("risk_score", 50.0) or 50.0)
        market_signal = float(p.get("market_signal_score", 55.0) or 55.0)

        score = 40 + min(cap_rate / 0.07, 1.0) * 25 + min(dscr / 1.4, 1.0) * 20 + (market_signal / 100) * 15
        score -= risk_score * 0.25
        score = max(0.0, min(score, 100.0))
        label = self.label(score)

        return AgentResult(
            agent_name=self.name,
            summary=f"Recommendation: {label}.",
            findings=[f"Investment score: {score:.1f}/100", f"Recommendation label: {label}"],
            risks=["Recommendation is only as reliable as uploaded documents and underwriting assumptions."],
            metrics={"investment_score": score, "recommendation_label": label},
            follow_up_questions=["Have all leases, rent rolls, T12s, and condition reports been uploaded?"],
            confidence=0.6,
        )
