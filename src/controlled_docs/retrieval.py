from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import date
from typing import Iterable

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from controlled_docs.audit import log_event
from controlled_docs.config import AppConfig
from controlled_docs.embeddings import Embedder, cosine_similarity
from controlled_docs.models import AccessPolicy, Chunk, Document, DocumentStatus, DocumentVersion
from controlled_docs.utils import tokenize

LOGGER = logging.getLogger(__name__)


@dataclass(slots=True)
class RetrievalQuery:
    role: str
    jurisdiction: str
    doc_type: str
    as_of_date: date
    question: str
    top_k: int
    include_nonapproved: bool = False


@dataclass(slots=True)
class RetrievalResult:
    document_id: str
    version_id: str
    version_number: int
    chunk_id: str
    snippet: str
    score: float
    citation: str
    title: str
    effective_date: str


class RetrievalService:
    def __init__(self, session: Session, config: AppConfig, embedder: Embedder):
        self.session = session
        self.config = config
        self.embedder = embedder

    def retrieve(self, query: RetrievalQuery) -> list[RetrievalResult]:
        policy = self.session.get(AccessPolicy, query.role)
        if policy is None:
            raise PermissionError(f"Unknown role: {query.role}")

        if query.jurisdiction not in policy.allowed_jurisdictions:
            raise PermissionError(f"Role {query.role} is not allowed for jurisdiction {query.jurisdiction}")
        if query.doc_type not in policy.allowed_doc_types:
            raise PermissionError(f"Role {query.role} is not allowed for doc_type {query.doc_type}")
        if query.include_nonapproved and query.role != "Auditor":
            raise PermissionError("Only Auditor may request DRAFT/OBSOLETE content")

        selected_versions = self._select_versions(query)
        if not selected_versions:
            self._log_query(query, [])
            return []

        chunks = self._load_chunks(version_ids=[version.version_id for version in selected_versions])
        query_embedding = self.embedder.embed_query(query.question)
        tokenized_question = set(tokenize(query.question))

        scored: list[RetrievalResult] = []
        for chunk in chunks:
            version = chunk.version
            document = version.document
            keyword_score = self._keyword_score(tokenized_question, chunk.text)
            vector_score = cosine_similarity(query_embedding, chunk.embedding)
            score = (0.45 * keyword_score) + (0.55 * vector_score)
            scored.append(
                RetrievalResult(
                    document_id=str(document.document_id),
                    version_id=str(version.version_id),
                    version_number=version.version_number,
                    chunk_id=str(chunk.chunk_id),
                    snippet=self._snippet(chunk.text, tokenized_question),
                    score=round(score, 4),
                    citation=(
                        f"[DOC:{document.document_id} VER:{version.version_number} CH:{chunk.chunk_id}]"
                    ),
                    title=document.title,
                    effective_date=str(version.effective_date),
                )
            )

        ranked = sorted(scored, key=lambda item: item.score, reverse=True)[: query.top_k]
        self._log_query(query, ranked)
        LOGGER.info("Retrieved %s chunks for question=%s", len(ranked), query.question)
        return ranked

    def _select_versions(self, query: RetrievalQuery) -> list[DocumentVersion]:
        statuses: Iterable[DocumentStatus]
        statuses = (
            [DocumentStatus.APPROVED, DocumentStatus.DRAFT, DocumentStatus.OBSOLETE]
            if query.include_nonapproved
            else [DocumentStatus.APPROVED]
        )

        documents = self.session.scalars(
            select(Document)
            .options(joinedload(Document.versions))
            .where(Document.jurisdiction == query.jurisdiction)
            .where(Document.doc_type == query.doc_type)
            .where(Document.status.in_(statuses))
        ).unique()

        selected_versions: list[DocumentVersion] = []
        for document in documents:
            effective_versions = [
                version for version in document.versions if version.effective_date <= query.as_of_date
            ]
            if not effective_versions:
                continue
            selected_versions.append(
                max(effective_versions, key=lambda version: (version.effective_date, version.version_number))
            )
        return selected_versions

    def _load_chunks(self, *, version_ids: list) -> list[Chunk]:
        return list(
            self.session.scalars(
                select(Chunk)
                .options(joinedload(Chunk.version).joinedload(DocumentVersion.document))
                .where(Chunk.version_id.in_(version_ids))
            )
        )

    @staticmethod
    def _keyword_score(question_tokens: set[str], text: str) -> float:
        text_tokens = set(tokenize(text))
        if not question_tokens:
            return 0.0
        return len(question_tokens.intersection(text_tokens)) / len(question_tokens)

    @staticmethod
    def _snippet(text: str, question_tokens: set[str]) -> str:
        sentences = [sentence.strip() for sentence in text.replace("\n", " ").split(".") if sentence.strip()]
        if not sentences:
            return text[:240]
        scored_sentences = sorted(
            sentences,
            key=lambda sentence: len(question_tokens.intersection(set(tokenize(sentence)))),
            reverse=True,
        )
        return f"{scored_sentences[0].strip()}."

    def _log_query(self, query: RetrievalQuery, results: list[RetrievalResult]) -> None:
        log_event(
            self.session,
            actor=query.role,
            action="QUERY_EXECUTED",
            object_type="retrieval",
            object_id=f"{query.role}:{query.jurisdiction}:{query.doc_type}:{query.as_of_date}",
            details={
                "question": query.question,
                "jurisdiction": query.jurisdiction,
                "doc_type": query.doc_type,
                "as_of_date": str(query.as_of_date),
                "include_nonapproved": query.include_nonapproved,
                "top_k_document_ids": [item.document_id for item in results],
            },
        )
        if query.include_nonapproved:
            log_event(
                self.session,
                actor=query.role,
                action="NONAPPROVED_OVERRIDE",
                object_type="retrieval",
                object_id=f"{query.role}:{query.jurisdiction}:{query.doc_type}",
                details={"question": query.question},
            )

