"""Lightweight retrieval utilities for document intelligence."""

from __future__ import annotations

import math
import re
from collections import Counter
from dataclasses import dataclass

from src.rag.document_processor import DocumentChunk


@dataclass(frozen=True)
class RetrievedChunk:
    """A retrieved chunk with a relevance score."""

    chunk: DocumentChunk
    score: float


class KeywordRetriever:
    """Simple dependency-light retriever used before vector search is configured."""

    token_pattern = re.compile(r"[a-zA-Z0-9$%.-]+")

    @classmethod
    def _tokens(cls, text: str) -> list[str]:
        return [token.lower() for token in cls.token_pattern.findall(text)]

    def retrieve(self, query: str, chunks: list[DocumentChunk], top_k: int = 5) -> list[RetrievedChunk]:
        """Rank chunks using cosine similarity over term counts."""
        query_counts = Counter(self._tokens(query))
        if not query_counts:
            return []
        results: list[RetrievedChunk] = []
        query_norm = math.sqrt(sum(value * value for value in query_counts.values()))
        for chunk in chunks:
            chunk_counts = Counter(self._tokens(chunk.content))
            dot = sum(query_counts[token] * chunk_counts.get(token, 0) for token in query_counts)
            chunk_norm = math.sqrt(sum(value * value for value in chunk_counts.values()))
            score = dot / (query_norm * chunk_norm) if query_norm and chunk_norm else 0.0
            if score > 0:
                results.append(RetrievedChunk(chunk=chunk, score=score))
        return sorted(results, key=lambda item: item.score, reverse=True)[:top_k]
