"""Rent roll agent."""

from src.agents.document_agents.base_document_agent import BaseDocumentAgent


class RentRollAgent(BaseDocumentAgent):
    """Analyze rent rolls for occupancy, rollover, and rent concentration."""

    name = "rent_roll_agent"
    focus_terms = ("unit", "tenant", "rent", "vacant", "lease", "expiration", "sqft", "deposit")
