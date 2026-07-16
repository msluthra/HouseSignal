"""RAG document intelligence page."""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import tempfile

import pandas as pd
import streamlit as st

from app.ui import apply_theme, hero
from src.rag.document_processor import DocumentProcessor
from src.rag.document_types import DOCUMENT_TYPE_LABELS, DocumentType
from src.rag.retriever import KeywordRetriever
from src.agents.base import AgentContext
from src.agents.router_agent import RouterAgent
from src.mock.sample_data import MOCK_DOCUMENTS, SAMPLE_DEAL

st.set_page_config(page_title="HouseSignal AI | Document Intelligence", layout="wide")
apply_theme()
hero(
    "Document Intelligence",
    "Test the RAG upload flow with bundled mock documents or your own non-sensitive sample file. The router sends each document type to a specialized agent.",
    pills=["Lease", "Rent roll", "Offering memo", "T12", "Condition report"],
)

processor = DocumentProcessor(chunk_size=650, chunk_overlap=80)
retriever = KeywordRetriever()
router = RouterAgent()

doc_options = list(DocumentType)
left, right = st.columns([0.9, 1.1])
with left:
    st.subheader("Document Source")
    source = st.radio("Use", ["Bundled mock document", "Upload sample file"], horizontal=True)
    doc_type = st.selectbox("Document Type", options=doc_options, format_func=lambda item: DOCUMENT_TYPE_LABELS[item])
    question = st.text_input("Question", value="What are the most important investment risks in this document?")
    uploaded_file = None
    if source == "Upload sample file":
        uploaded_file = st.file_uploader("Upload PDF, TXT, CSV, or Markdown", type=["pdf", "txt", "csv", "md"])

    analyze = st.button("Run Document Agent", type="primary", use_container_width=True)

with right:
    st.subheader("Current Deal Context")
    st.write(f"**{SAMPLE_DEAL.name}**")
    st.write(f"{SAMPLE_DEAL.units} units · {SAMPLE_DEAL.asset_type} · {SAMPLE_DEAL.city}, {SAMPLE_DEAL.state}")
    st.caption("This context is mock data and is passed only as deal context, not as a real document source.")

processed = None
agent_result = None
retrieved = []

if analyze:
    if source == "Bundled mock document":
        text = MOCK_DOCUMENTS[doc_type.value]
        chunks = processor.chunk_text(f"mock-{doc_type.value}", doc_type, text)
        retrieved = retriever.retrieve(question, chunks, top_k=4)
        context = AgentContext(
            question=question,
            property_profile=SAMPLE_DEAL.to_agent_profile(),
            retrieved_chunks=[item.chunk for item in retrieved],
        )
        agent_result = router.run(doc_type.value, context)
        st.success(f"Loaded bundled {DOCUMENT_TYPE_LABELS[doc_type]} sample: {len(chunks)} chunks")
    elif uploaded_file is not None:
        suffix = Path(uploaded_file.name).suffix
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp.write(uploaded_file.getbuffer())
            tmp_path = tmp.name
        try:
            processed = processor.process(tmp_path, doc_type)
            retrieved = retriever.retrieve(question, processed.chunks, top_k=4)
            context = AgentContext(
                question=question,
                property_profile=SAMPLE_DEAL.to_agent_profile(),
                retrieved_chunks=[item.chunk for item in retrieved],
            )
            agent_result = router.run(doc_type.value, context)
            st.success(f"Processed {processed.file_name}: {len(processed.chunks)} chunks")
        finally:
            Path(tmp_path).unlink(missing_ok=True)
    else:
        st.warning("Upload a sample file or switch to the bundled mock document option.")

if agent_result:
    st.subheader(agent_result.agent_name.replace("_", " ").title())
    k1, k2, k3 = st.columns(3)
    k1.metric("Confidence", f"{agent_result.confidence * 100:.0f}%")
    k2.metric("Retrieved Chunks", len(retrieved))
    k3.metric("Findings", len(agent_result.findings))

    st.write(agent_result.summary)
    col_a, col_b = st.columns([1, 1])
    with col_a:
        st.markdown("#### Findings")
        for finding in agent_result.findings:
            st.write(f"- {finding}")
    with col_b:
        st.markdown("#### Risks / Follow-ups")
        for risk in agent_result.risks:
            st.warning(risk)
        for question_item in agent_result.follow_up_questions:
            st.write(f"- {question_item}")

    st.markdown("#### Retrieved Evidence")
    evidence_rows = [
        {
            "score": round(item.score, 3),
            "chunk": item.chunk.chunk_index,
            "text": item.chunk.content[:320] + ("..." if len(item.chunk.content) > 320 else ""),
        }
        for item in retrieved
    ]
    st.dataframe(pd.DataFrame(evidence_rows), use_container_width=True)
else:
    st.info("Choose a document type and run the agent to see retrieval evidence, findings, and risks.")
