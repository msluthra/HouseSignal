"""Base classes for HouseSignal AI agents."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol

from src.rag.document_processor import DocumentChunk


@dataclass(frozen=True)
class AgentContext:
    """Shared context passed to agents."""

    question: str = ""
    property_profile: dict[str, Any] = field(default_factory=dict)
    retrieved_chunks: list[DocumentChunk] = field(default_factory=list)
    market_snapshot: dict[str, Any] = field(default_factory=dict)
    assumptions: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class AgentResult:
    """Structured output from an agent."""

    agent_name: str
    summary: str
    findings: list[str]
    risks: list[str] = field(default_factory=list)
    metrics: dict[str, float | str] = field(default_factory=dict)
    follow_up_questions: list[str] = field(default_factory=list)
    confidence: float = 0.5


class Agent(Protocol):
    """Protocol implemented by all HouseSignal agents."""

    name: str

    def run(self, context: AgentContext) -> AgentResult:
        """Run the agent and return structured findings."""
