from __future__ import annotations

from controlled_docs.config import AppConfig
from controlled_docs.embeddings import get_embedder
from controlled_docs.qa import AskQuery, QAService
from controlled_docs.retrieval import RetrievalQuery, RetrievalService
from controlled_docs.utils import parse_date


def test_retrieval_honors_as_of_date(populated_session, app_config: AppConfig) -> None:
    retrieval_service = RetrievalService(populated_session, app_config, get_embedder(app_config))
    results_old = retrieval_service.retrieve(
        RetrievalQuery(
            role="Analyst",
            jurisdiction="US-FDA",
            doc_type="SOP",
            as_of_date=parse_date("2024-06-30"),
            question="Within how many business days must batch records be reviewed after manufacturing completion?",
            top_k=5,
        )
    )
    results_new = retrieval_service.retrieve(
        RetrievalQuery(
            role="Analyst",
            jurisdiction="US-FDA",
            doc_type="SOP",
            as_of_date=parse_date("2026-01-15"),
            question="Within how many business days must batch records be reviewed after manufacturing completion?",
            top_k=5,
        )
    )

    assert any("VER:1" in result.citation for result in results_old)
    assert any("VER:2" in result.citation for result in results_new)


def test_qa_returns_citations(populated_session, app_config: AppConfig) -> None:
    qa_service = QAService(RetrievalService(populated_session, app_config, get_embedder(app_config)))
    result = qa_service.ask(
        AskQuery(
            role="Analyst",
            jurisdiction="US-FDA",
            doc_type="SOP",
            as_of_date=parse_date("2026-01-15"),
            question="Within how many business days must batch records be reviewed after manufacturing completion?",
            top_k=5,
        )
    )

    assert "1 business day" in result["answer"]
    assert result["citations"]

