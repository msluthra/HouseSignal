"""Document extraction and chunking utilities for RAG workflows."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path

from src.rag.document_types import DocumentType


@dataclass(frozen=True)
class DocumentChunk:
    """One text chunk prepared for retrieval."""

    document_id: str
    chunk_index: int
    content: str
    metadata: dict[str, str]


@dataclass(frozen=True)
class ProcessedDocument:
    """Parsed document payload."""

    document_id: str
    document_type: DocumentType
    file_name: str
    content_sha256: str
    text: str
    chunks: list[DocumentChunk]


class DocumentProcessor:
    """Extract text and build chunks for supported document files."""

    def __init__(self, chunk_size: int = 1200, chunk_overlap: int = 160) -> None:
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    @staticmethod
    def _sha256_bytes(data: bytes) -> str:
        return hashlib.sha256(data).hexdigest()

    def extract_text(self, file_path: str | Path) -> str:
        """Extract text from TXT/CSV/PDF files.

        PDF extraction uses pypdf lazily so import checks do not require PDF
        dependencies unless this path is used.
        """
        path = Path(file_path)
        data = path.read_bytes()
        suffix = path.suffix.lower()
        if suffix in {".txt", ".csv", ".md"}:
            return data.decode("utf-8", errors="ignore")
        if suffix == ".pdf":
            from pypdf import PdfReader

            reader = PdfReader(str(path))
            return "\n".join(page.extract_text() or "" for page in reader.pages)
        raise ValueError(f"Unsupported document file type: {suffix}")

    def chunk_text(self, document_id: str, document_type: DocumentType, text: str) -> list[DocumentChunk]:
        """Split text into overlapping chunks for retrieval."""
        cleaned = "\n".join(line.strip() for line in text.splitlines() if line.strip())
        chunks: list[DocumentChunk] = []
        start = 0
        chunk_index = 0
        while start < len(cleaned):
            end = min(start + self.chunk_size, len(cleaned))
            content = cleaned[start:end]
            chunks.append(
                DocumentChunk(
                    document_id=document_id,
                    chunk_index=chunk_index,
                    content=content,
                    metadata={"document_type": document_type.value},
                )
            )
            if end == len(cleaned):
                break
            start = max(0, end - self.chunk_overlap)
            chunk_index += 1
        return chunks

    def process(self, file_path: str | Path, document_type: DocumentType) -> ProcessedDocument:
        """Extract and chunk a document file."""
        path = Path(file_path)
        data = path.read_bytes()
        content_hash = self._sha256_bytes(data)
        document_id = content_hash[:16]
        text = self.extract_text(path)
        chunks = self.chunk_text(document_id, document_type, text)
        return ProcessedDocument(
            document_id=document_id,
            document_type=document_type,
            file_name=path.name,
            content_sha256=content_hash,
            text=text,
            chunks=chunks,
        )
