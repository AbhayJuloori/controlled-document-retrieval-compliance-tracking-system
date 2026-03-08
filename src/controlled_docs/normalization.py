from __future__ import annotations

from dataclasses import dataclass

from controlled_docs.models import DocumentStatus


JURISDICTION_MAP = {
    "US FDA": "US-FDA",
    "FDA": "US-FDA",
    "US-FDA": "US-FDA",
    "EU MDR": "EU-MDR",
    "EU-MDR": "EU-MDR",
    "ISO 13485": "ISO13485",
    "ISO13485": "ISO13485",
}

DOC_TYPE_MAP = {
    "SOP": "SOP",
    "STANDARD OPERATING PROCEDURE": "SOP",
    "WI": "WI",
    "WORK INSTRUCTION": "WI",
    "POLICY": "POLICY",
    "POLICY MEMO": "POLICY",
    "TRAINING": "TRAINING",
    "TRAINING RECORD": "TRAINING",
    "CAPA": "CAPA",
    "CAPA SUMMARY": "CAPA",
}


@dataclass(slots=True)
class NormalizedMetadata:
    document_key: str
    title: str
    doc_type: str
    jurisdiction: str
    owner: str
    status: DocumentStatus


def normalize_jurisdiction(value: str) -> str:
    normalized = JURISDICTION_MAP.get(value.strip().upper(), value.strip().upper())
    if normalized not in {"US-FDA", "EU-MDR", "ISO13485"}:
        raise ValueError(f"Unsupported jurisdiction: {value}")
    return normalized


def normalize_doc_type(value: str) -> str:
    normalized = DOC_TYPE_MAP.get(value.strip().upper(), value.strip().upper())
    if normalized not in {"SOP", "WI", "POLICY", "TRAINING", "CAPA"}:
        raise ValueError(f"Unsupported doc_type: {value}")
    return normalized


def normalize_metadata(
    *,
    document_key: str,
    title: str,
    doc_type: str,
    jurisdiction: str,
    owner: str,
    status: str,
) -> NormalizedMetadata:
    if not document_key.strip():
        raise ValueError("document_key is required")
    if not title.strip():
        raise ValueError("title is required")
    if not owner.strip():
        raise ValueError("owner is required")
    return NormalizedMetadata(
        document_key=document_key.strip(),
        title=title.strip(),
        doc_type=normalize_doc_type(doc_type),
        jurisdiction=normalize_jurisdiction(jurisdiction),
        owner=owner.strip(),
        status=DocumentStatus(status.strip().upper()),
    )

