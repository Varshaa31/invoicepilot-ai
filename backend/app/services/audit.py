from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.entities import AuditLog


def add_audit(db: Session, invoice_id: UUID, event_type: str, metadata: dict | None = None) -> AuditLog:
    log = AuditLog(
        invoice_id=invoice_id,
        event_type=event_type,
        event_metadata=metadata,
        created_at=datetime.now(timezone.utc),
    )
    db.add(log)
    return log
