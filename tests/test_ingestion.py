from __future__ import annotations

from sqlalchemy import func, select

from controlled_docs.models import AuditLog, Chunk, Document, DocumentVersion


def test_ingestion_persists_documents_versions_and_chunks(populated_session) -> None:
    document_count = populated_session.scalar(select(func.count()).select_from(Document))
    version_count = populated_session.scalar(select(func.count()).select_from(DocumentVersion))
    chunk_count = populated_session.scalar(select(func.count()).select_from(Chunk))
    audit_count = populated_session.scalar(select(func.count()).select_from(AuditLog))

    assert document_count == 12
    assert version_count == 22
    assert chunk_count > 22
    assert audit_count >= version_count
