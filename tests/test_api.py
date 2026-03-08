from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from controlled_docs.db import initialize_database, session_scope
from controlled_docs.embeddings import get_embedder
from controlled_docs.ingestion import IngestionService
from controlled_docs.server import create_app
from data.generate_synthetic_data import generate_docs


def test_ask_endpoint_returns_structured_response(app_config) -> None:
    project_root = Path(__file__).resolve().parents[1]
    generate_docs()
    session_factory = initialize_database(app_config)
    with session_scope(session_factory) as session:
        IngestionService(session, app_config, get_embedder(app_config)).ingest_register(
            project_root / "data" / "document_register.xlsx", actor="pytest"
        )
    client = TestClient(create_app(app_config))
    response = client.post(
        "/ask",
        json={
            "role": "Analyst",
            "jurisdiction": "US-FDA",
            "doc_type": "SOP",
            "as_of": "2026-01-15",
            "question": "Within how many business days must batch records be reviewed after manufacturing completion?",
            "top_k": 3,
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["citations"]
    assert "answer" in payload
