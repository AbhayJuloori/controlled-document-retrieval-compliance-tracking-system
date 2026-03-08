from __future__ import annotations

from fastapi import FastAPI

from controlled_docs.config import AppConfig
from controlled_docs.db import initialize_database, session_scope
from controlled_docs.embeddings import get_embedder
from controlled_docs.logging_utils import configure_logging
from controlled_docs.qa import AskQuery, QAService
from controlled_docs.retrieval import RetrievalService
from controlled_docs.schemas import AskRequest, AskResponse
from controlled_docs.utils import parse_date


def create_app(config: AppConfig | None = None) -> FastAPI:
    app_config = config or AppConfig.from_env()
    configure_logging(app_config.log_level)
    session_factory = initialize_database(app_config)
    embedder = get_embedder(app_config)

    app = FastAPI(title="Controlled Document Retrieval & Compliance Tracking System")

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.post("/ask", response_model=AskResponse)
    def ask(request: AskRequest) -> AskResponse:
        with session_scope(session_factory) as session:
            qa_service = QAService(RetrievalService(session, app_config, embedder))
            result = qa_service.ask(
                AskQuery(
                    role=request.role,
                    jurisdiction=request.jurisdiction,
                    doc_type=request.doc_type,
                    as_of_date=parse_date(request.as_of),
                    question=request.question,
                    top_k=request.top_k,
                    include_nonapproved=request.include_nonapproved,
                )
            )
            return AskResponse(
                answer=result["answer"],
                citations=result["citations"],
                searched=result["searched"],
                results=result["results"],
            )

    return app

