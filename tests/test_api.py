from pathlib import Path

from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app


def build_settings(tmp_path: Path) -> Settings:
    return Settings(
        upload_dir=tmp_path / "uploads",
        document_dir=tmp_path / "documents",
        chunk_size=180,
        chunk_overlap=40,
        top_k=2,
    )


def test_health_endpoint_reports_empty_index(tmp_path: Path) -> None:
    app = create_app(build_settings(tmp_path))

    with TestClient(app) as client:
        response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "documents_indexed": 0,
        "chunks_indexed": 0,
    }


def test_ingest_text_and_answer_question(tmp_path: Path) -> None:
    app = create_app(build_settings(tmp_path))

    with TestClient(app) as client:
        ingest_response = client.post(
            "/documents/ingest-text",
            json={
                "source": "facts.txt",
                "text": (
                    "FastAPI is a Python web framework for building APIs quickly. "
                    "Streamlit is useful for lightweight data apps and demos."
                ),
            },
        )
        answer_response = client.post("/qa/ask", json={"question": "What is FastAPI?"})

    assert ingest_response.status_code == 200
    assert ingest_response.json()["chunks_added"] >= 1

    assert answer_response.status_code == 200
    payload = answer_response.json()
    assert "FastAPI is a Python web framework for building APIs quickly." in payload["answer"]
    assert payload["sources"][0]["source"] == "facts.txt"


def test_upload_txt_file_indexes_document(tmp_path: Path) -> None:
    app = create_app(build_settings(tmp_path))

    with TestClient(app) as client:
        response = client.post(
            "/documents/upload",
            files={"file": ("company.txt", b"Acme Corp uses FastAPI for its internal QA assistant.")},
        )
        documents_response = client.get("/documents")

    assert response.status_code == 200
    assert response.json()["source"] == "company.txt"
    assert "company.txt" in documents_response.json()["documents"]
