from __future__ import annotations

import os

import httpx
import streamlit as st


DEFAULT_API_URL = os.getenv("SMART_QA_API_URL", "http://127.0.0.1:8000").rstrip("/")


def api_request(method: str, path: str, **kwargs) -> dict[str, object]:
    url = f"{st.session_state.api_url.rstrip('/')}{path}"
    with httpx.Client(timeout=20.0) as client:
        response = client.request(method, url, **kwargs)
        response.raise_for_status()
        return response.json()


st.set_page_config(page_title="Smart QA System", page_icon="Q", layout="wide")
st.title("Smart QA System")
st.caption("Upload documents, index text, and ask questions against the stored knowledge base.")

if "api_url" not in st.session_state:
    st.session_state.api_url = DEFAULT_API_URL

with st.sidebar:
    st.subheader("Backend")
    st.session_state.api_url = st.text_input("API URL", value=st.session_state.api_url)
    if st.button("Check Health", use_container_width=True):
        try:
            health = api_request("GET", "/health")
            st.success(
                f"Backend is healthy. Documents: {health['documents_indexed']}, chunks: {health['chunks_indexed']}"
            )
        except httpx.HTTPError as exc:
            st.error(f"Unable to reach API: {exc}")

col1, col2 = st.columns(2)

with col1:
    st.subheader("Upload a Document")
    upload = st.file_uploader("Supported formats: .txt, .md, .pdf, .docx", type=["txt", "md", "pdf", "docx"])
    if st.button("Upload and Index", use_container_width=True, disabled=upload is None):
        try:
            file_payload = {"file": (upload.name, upload.getvalue(), upload.type or "application/octet-stream")}
            result = api_request("POST", "/documents/upload", files=file_payload)
            st.success(f"Indexed {result['source']} with {result['chunks_added']} chunks.")
        except httpx.HTTPError as exc:
            st.error(f"Upload failed: {exc}")

with col2:
    st.subheader("Paste Text")
    text_source = st.text_input("Source name", value="notes.txt")
    text_payload = st.text_area("Text to index", height=220, placeholder="Paste text here...")
    if st.button("Index Text", use_container_width=True, disabled=not text_payload.strip()):
        try:
            result = api_request(
                "POST",
                "/documents/ingest-text",
                json={"text": text_payload, "source": text_source or "notes.txt"},
            )
            st.success(f"Indexed {result['source']} with {result['chunks_added']} chunks.")
        except httpx.HTTPError as exc:
            st.error(f"Indexing failed: {exc}")

st.subheader("Ask a Question")
question = st.text_input("Question", placeholder="What does the document say about ...?")
if st.button("Ask", use_container_width=True, disabled=not question.strip()):
    try:
        result = api_request("POST", "/qa/ask", json={"question": question})
        st.markdown("**Answer**")
        st.write(result["answer"])

        if result["sources"]:
            st.markdown("**Sources**")
            for source in result["sources"]:
                st.write(f"- {source['source']} (score: {source['score']})")

        if result["matches"]:
            st.markdown("**Matched Chunks**")
            for match in result["matches"]:
                with st.expander(f"{match['source']} | score {match['score']}"):
                    st.write(match["text"])
    except httpx.HTTPError as exc:
        st.error(f"Question failed: {exc}")
