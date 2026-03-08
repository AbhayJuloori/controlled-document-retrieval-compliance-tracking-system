from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import date
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from controlled_docs.config import AppConfig
from controlled_docs.models import Document, DocumentStatus
from controlled_docs.utils import ensure_parent_dir


REAPPROVAL_WINDOWS = {
    "SOP": 365,
    "WI": 180,
    "POLICY": 365,
    "TRAINING": 180,
    "CAPA": 120,
}


@dataclass(slots=True)
class ComplianceFlag:
    document_id: str
    title: str
    status: str
    effective_date: str
    days_since_review: int
    risk_flag: str


def build_compliance_dashboard(
    session: Session, config: AppConfig, *, as_of_date: date, output_path: Path
) -> list[ComplianceFlag]:
    documents = list(
        session.scalars(
            select(Document).options(joinedload(Document.versions)).order_by(Document.title.asc())
        ).unique()
    )
    rows: list[ComplianceFlag] = []
    for document in documents:
        versions = sorted(document.versions, key=lambda version: (version.effective_date, version.version_number))
        effective_versions = [version for version in versions if version.effective_date <= as_of_date]
        if not effective_versions:
            rows.append(
                ComplianceFlag(
                    document_id=str(document.document_id),
                    title=document.title,
                    status=document.status.value,
                    effective_date="N/A",
                    days_since_review=-1,
                    risk_flag="NO_EFFECTIVE_VERSION",
                )
            )
            continue

        current = effective_versions[-1]
        days_since_review = (as_of_date - current.effective_date).days
        window = REAPPROVAL_WINDOWS.get(document.doc_type, config.review_window_days)
        if document.status == DocumentStatus.DRAFT:
            risk_flag = "DRAFT_IN_CONTROLLED_SET"
        elif document.status == DocumentStatus.OBSOLETE:
            risk_flag = "OBSOLETE_ACTIVE_REFERENCE"
        elif days_since_review > window:
            risk_flag = "REAPPROVAL_OVERDUE"
        else:
            risk_flag = "OK"
        rows.append(
            ComplianceFlag(
                document_id=str(document.document_id),
                title=document.title,
                status=document.status.value,
                effective_date=str(current.effective_date),
                days_since_review=days_since_review,
                risk_flag=risk_flag,
            )
        )

    ensure_parent_dir(output_path)
    with output_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "document_id",
                "title",
                "status",
                "effective_date",
                "days_since_review",
                "risk_flag",
            ],
        )
        writer.writeheader()
        for row in rows:
            writer.writerow(row.__dict__)
    return rows

