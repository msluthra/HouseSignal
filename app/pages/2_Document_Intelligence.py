"""RAG document intelligence page."""

from __future__ import annotations

import tempfile
from pathlib import Path

import streamlit as st

from src.rag.document_types import DOCUMENT_TYPE_LABELS, DocumentType
from src.services.document_intelligence import DocumentIntelligenceService

st.set_page_config(page_title="Document Intelligence", layout="wide")
st.title("Document Intelligence")
st.caption("Upload CRE diligence documents and route them to specialized document agents.")

doc_type = st.selectbox(
    "Document Type",
    options=list(DocumentType),
    format_func=lambda item: DOCUMENT_TYPE_LABELS[item],
)
question = st.text_input("Question", value="What are the most important investment risks in this document?")
uploaded_file = st.file_uploader("Upload PDF, TXT, CSV, or Markdown", type=["pdf", "txt", "csv", "md"])

if uploaded_file and st.button("Analyze Document", type="primary"):
    suffix = Path(uploaded_file.name).suffix
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(uploaded_file.getbuffer())
        tmp_path = tmp.name
    try:
        processed, result = DocumentIntelligenceService().analyze_file(tmp_path, doc_type, question)
        st.success(f"Processed {processed.file_name}: {len(processed.chunks)} chunks")
        st.subheader(result.agent_name.replace("_", " ").title())
        st.write(result.summary)
        st.write("Findings")
        for finding in result.findings:
            st.write(f"- {finding}")
        if result.risks:
            st.write("Risks")
            for risk in result.risks:
                st.warning(risk)
    finally:
        Path(tmp_path).unlink(missing_ok=True)
