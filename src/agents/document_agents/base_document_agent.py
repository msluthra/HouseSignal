"""Base implementation for document-specific agents."""

from __future__ import annotations

from src.agents.base import AgentContext, AgentResult


class BaseDocumentAgent:
    """Extract conservative findings from retrieved document chunks."""

    name = "base_document_agent"
    focus_terms: tuple[str, ...] = ()

    def _matching_lines(self, context: AgentContext) -> list[str]:
        lines: list[str] = []
        for chunk in context.retrieved_chunks:
            for line in chunk.content.splitlines():
                lowered = line.lower()
                if any(term in lowered for term in self.focus_terms):
                    lines.append(line.strip())
        return lines[:8]

    def run(self, context: AgentContext) -> AgentResult:
        """Return findings from retrieved chunks and flag missing evidence."""
        matches = self._matching_lines(context)
        findings = matches or ["No high-confidence matching clauses or rows were found in the retrieved context."]
        risks = [] if matches else ["Document may need manual review or better OCR/table extraction."]
        return AgentResult(
            agent_name=self.name,
            summary=f"Reviewed {len(context.retrieved_chunks)} retrieved chunks for {self.name.replace('_', ' ')} evidence.",
            findings=findings,
            risks=risks,
            follow_up_questions=["Is this document complete and final?", "Are there exhibits or schedules missing?"],
            confidence=0.7 if matches else 0.35,
        )
