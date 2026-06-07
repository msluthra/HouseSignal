"""Lease agreement agent."""

from src.agents.document_agents.base_document_agent import BaseDocumentAgent


class LeaseAgreementAgent(BaseDocumentAgent):
    """Analyze lease agreements for income and legal risk signals."""

    name = "lease_agreement_agent"
    focus_terms = ("rent", "term", "renewal", "default", "termination", "assignment", "sublet", "expense")
