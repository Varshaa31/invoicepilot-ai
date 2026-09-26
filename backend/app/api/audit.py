from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.entities import AuditLog, User, InvoiceStatus
from app.schemas.common import AuditLogOut, DashboardOut
from app.services.catalog import dashboard_stats
from app.services.invoices import get_invoice_or_404
from app.core.dependencies import get_current_user

router = APIRouter(tags=["audit"])


@router.get("/audit/{invoice_id}", response_model=list[AuditLogOut])
def get_audit(invoice_id: UUID, db: Session = Depends(get_db)) -> list[AuditLogOut]:
    get_invoice_or_404(db, invoice_id)
    rows = db.execute(
        select(AuditLog).where(AuditLog.invoice_id == invoice_id).order_by(AuditLog.created_at)
    ).scalars().all()
    return [
        AuditLogOut(
            id=row.id,
            invoice_id=row.invoice_id,
            event_type=row.event_type,
            metadata=row.event_metadata,
            created_at=row.created_at,
        )
        for row in rows
    ]


@router.get("/dashboard")
def dashboard(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return dashboard_stats(db, user)