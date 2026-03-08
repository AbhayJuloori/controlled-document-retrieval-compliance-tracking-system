from __future__ import annotations

from pathlib import Path

import pytest

from controlled_docs.config import AppConfig
from controlled_docs.db import initialize_database, session_scope
from controlled_docs.embeddings import get_embedder
from controlled_docs.ingestion import IngestionService
from data.generate_synthetic_data import generate_docs


@pytest.fixture()
def app_config(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> AppConfig:
    monkeypatch.chdir(tmp_path)
    (tmp_path / "artifacts").mkdir(parents=True, exist_ok=True)
    config = AppConfig(
        database_url=f"sqlite:///{tmp_path / 'artifacts' / 'test.db'}",
        embedding_backend="local",
        chunk_size=90,
        chunk_overlap=15,
        retrieval_top_k=5,
        log_level="INFO",
    )
    return config


@pytest.fixture()
def populated_session(app_config: AppConfig, tmp_path: Path):
    project_root = Path(__file__).resolve().parents[1]
    generate_docs()
    session_factory = initialize_database(app_config)
    embedder = get_embedder(app_config)
    with session_scope(session_factory) as session:
        service = IngestionService(session, app_config, embedder)
        service.ingest_register(project_root / "data" / "document_register.xlsx", actor="pytest")
        yield session

