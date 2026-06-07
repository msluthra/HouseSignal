"""High-level document intelligence workflow."""

from __future__ import annotations

from pathlib import Path

from src.agents.base import AgentContext, AgentResult
from src.agents.router_agent import RouterAgent
from src.rag.document_processor import DocumentProcessor, ProcessedDocument
from src.rag.document_types import DocumentType
from src.rag.retriever import KeywordRetriever


class DocumentIntelligenceService:
    """Process, retrieve, and analyze uploaded CRE documents."""

    def __init__(self) -> None:
        self.processor = DocumentProcessor()
        self.retriever = KeywordRetriever()
        self.router = RouterAgent()

    def analyze_file(self, file_path: str | Path, document_type: DocumentType, question: str) -> tuple[ProcessedDocument, AgentResult]:
        """Analyze one document using the matching specialized agent."""
        processed = self.processor.process(file_path, document_type)
        retrieved = self.retriever.retrieve(question, processed.chunks, top_k=5)
        context = AgentContext(question=question, retrieved_chunks=[item.chunk for item in retrieved])
        result = self.router.run(document_type.value, context)
        return processed, result
