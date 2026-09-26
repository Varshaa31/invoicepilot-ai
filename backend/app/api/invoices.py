from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user
from app.db.session import get_db
from app.models.entities import InvoiceStatus, User
from app.schemas.common import (
    InvoiceCreateIn,
    InvoiceListOut,
    InvoiceOut,
    InvoiceUpdateIn,
    ResolveServiceIn,
)
from app.services.invoices import (
    approve_invoice,
    calculate_existing,
    create_invoice,
    get_invoice_or_404,
    list_invoices,
    mark_exported,
    resolve_item_service,
    serialize_invoice,
    to_list_item,
    update_invoice,
)
from app.services.matching import load_catalog
from app.services.pdf import generate_invoice_pdf

router = APIRouter(
    prefix="/invoices",
    tags=["invoices"],
)


@router.post("", response_model=InvoiceOut, status_code=201)
def create(
    payload: InvoiceCreateIn,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> InvoiceOut:
    invoice = create_invoice(
        db,
        payload,
        user,
    )

    return serialize_invoice(
        invoice,
        load_catalog(db, user),
    )


@router.get("", response_model=list[InvoiceListOut])
def list_all(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
    status: InvoiceStatus | None = None,
    customer: str | None = None,
    date_from: datetime | None = None,
    date_to: datetime | None = None,
) -> list[InvoiceListOut]:
    return [
        to_list_item(row)
        for row in list_invoices(
            db,
            user,
            status,
            customer,
            date_from,
            date_to,
        )
    ]


@router.get(
    "/{invoice_id}",
    response_model=InvoiceOut,
)
def get_one(
    invoice_id: UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> InvoiceOut:
    invoice = get_invoice_or_404(
        db,
        invoice_id,
        user,
    )

    return serialize_invoice(
        invoice,
        load_catalog(db, user),
    )


@router.put(
    "/{invoice_id}",
    response_model=InvoiceOut,
)
def update(
    invoice_id: UUID,
    payload: InvoiceUpdateIn,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> InvoiceOut:
    invoice = update_invoice(
        db,
        invoice_id,
        payload,
        user,
    )

    return serialize_invoice(
        invoice,
        load_catalog(db, user),
    )


@router.post(
    "/{invoice_id}/resolve-service",
    response_model=InvoiceOut,
)
def resolve_service(
    invoice_id: UUID,
    payload: ResolveServiceIn,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> InvoiceOut:
    invoice = resolve_item_service(
        db,
        invoice_id,
        payload.item_id,
        payload.service_id,
        user,
    )

    return serialize_invoice(
        invoice,
        load_catalog(db, user),
    )


@router.post(
    "/{invoice_id}/calculate",
    response_model=InvoiceOut,
)
def calculate(
    invoice_id: UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> InvoiceOut:
    invoice = calculate_existing(
        db,
        invoice_id,
        user,
    )

    return serialize_invoice(
        invoice,
        load_catalog(db, user),
    )


@router.post(
    "/{invoice_id}/approve",
    response_model=InvoiceOut,
)
def approve(
    invoice_id: UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> InvoiceOut:
    invoice = approve_invoice(
        db,
        invoice_id,
        user,
    )

    return serialize_invoice(
        invoice,
        load_catalog(db, user),
    )


@router.get("/{invoice_id}/pdf")
def download_pdf(
    invoice_id: UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
    persist: bool = Query(default=True),
):
    invoice = get_invoice_or_404(
        db,
        invoice_id,
        user,
    )

    pdf_bytes = generate_invoice_pdf(invoice)

    if (
        persist
        and invoice.status == InvoiceStatus.APPROVED
    ):
        mark_exported(
            db,
            invoice.id,
            user,
        )

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": (
                f'attachment; '
                f'filename="{invoice.invoice_number}.pdf"'
            )
        },
    )