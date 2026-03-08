from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session
from uuid import uuid4

from controlled_docs.models import AuditLog
def log_event(
    session: Session,
    *,
    actor: str,
    action: str,
    object_type: str,
    object_id: str,
    details: dict[str, Any],
) -> AuditLog:
    event = AuditLog(
        event_id=uuid4(),
        actor=actor,
        action=action,
        object_type=object_type,
        object_id=object_id,
        details=details,
    )
    session.add(event)
    return event
