"""Financial analysis agent for commercial real estate underwriting."""

from __future__ import annotations

from src.agents.base import AgentContext, AgentResult


class FinancialAnalysisAgent:
    """Compute core CRE underwriting metrics from provided assumptions."""

    name = "financial_analysis_agent"

    def run(self, context: AgentContext) -> AgentResult:
        """Estimate NOI, cap rate, DSCR, and cash-on-cash return."""
        p = context.property_profile
        gross_income = float(p.get("annual_gross_income", 0.0) or 0.0)
        expenses = float(p.get("annual_operating_expenses", 0.0) or 0.0)
        purchase_price = float(p.get("purchase_price", 0.0) or 0.0)
        debt_service = float(p.get("annual_debt_service", 0.0) or 0.0)
        equity = float(p.get("equity_invested", 0.0) or 0.0)

        noi = gross_income - expenses
        cap_rate = noi / purchase_price if purchase_price else 0.0
        dscr = noi / debt_service if debt_service else 0.0
        cash_on_cash = (noi - debt_service) / equity if equity else 0.0

        findings = [
            f"Estimated NOI: ${noi:,.0f}",
            f"Estimated cap rate: {cap_rate * 100:.2f}%",
            f"Estimated DSCR: {dscr:.2f}x" if debt_service else "Debt service not provided, DSCR not calculated.",
            f"Estimated cash-on-cash return: {cash_on_cash * 100:.2f}%" if equity else "Equity invested not provided, cash-on-cash not calculated.",
        ]
        risks = []
        if dscr and dscr < 1.2:
            risks.append("Debt service coverage is thin under current assumptions.")
        if cap_rate and cap_rate < 0.045:
            risks.append("Cap rate appears low, so appreciation assumptions matter more.")

        return AgentResult(
            agent_name=self.name,
            summary="Calculated first-pass commercial underwriting metrics.",
            findings=findings,
            risks=risks,
            metrics={"noi": noi, "cap_rate": cap_rate, "dscr": dscr, "cash_on_cash": cash_on_cash},
            confidence=0.65,
        )
