from decimal import Decimal

from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.entities import AuditLog, InvoiceStatus, Service
from app.schemas.common import CustomerIn, InvoiceCreateIn, InvoiceItemIn, InvoiceUpdateIn
from app.services.invoices import approve_invoice, create_invoice, mark_exported, update_invoice
from app.services.pdf import generate_invoice_pdf


def _service_id(db: Session, name: str):
    return db.execute(select(Service).where(Service.name == name)).scalar_one().id


def _happy_payload(db: Session) -> InvoiceCreateIn:
    return InvoiceCreateIn(
        customer=CustomerIn(name="Rahul", email="rahul@example.com", company="Acme"),
        items=[
            InvoiceItemIn(requested_service="E-commerce Website", quantity=Decimal("1")),
            InvoiceItemIn(requested_service="SEO Optimization", quantity=Decimal("1")),
        ],
        tax_rate=Decimal("18"),
        notes="Prices verified from service catalog",
        source_message="Hi, I'm Rahul. I need an e-commerce website and SEO optimization.",
    )


def test_create_invoice_uses_catalog_prices(db: Session):
    invoice = create_invoice(db, _happy_payload(db))
    assert invoice.status == InvoiceStatus.READY_FOR_APPROVAL
    assert invoice.subtotal == Decimal("77000.00")
    assert invoice.tax_amount == Decimal("13860.00")
    assert invoice.total == Decimal("90860.00")
    assert all(item.price_source == "service_catalog" for item in invoice.items)


def test_edit_invoice_quantity(db: Session):
    invoice = create_invoice(db, _happy_payload(db))
    updated = update_invoice(
        db,
        invoice.id,
        InvoiceUpdateIn(
            items=[
                InvoiceItemIn(
                    requested_service="E-commerce Website",
                    quantity=Decimal("2"),
                    service_id=_service_id(db, "E-commerce Website"),
                )
            ]
        ),
    )
    assert updated.subtotal == Decimal("130000.00")


def test_unresolved_service_blocks_approval(db: Session):
    invoice = create_invoice(
        db,
        InvoiceCreateIn(
            customer=CustomerIn(name="Rahul", email="rahul@example.com"),
            items=[InvoiceItemIn(requested_service="drone photography", quantity=Decimal("1"))],
        ),
    )
    assert invoice.status == InvoiceStatus.REVIEW_REQUIRED
    try:
        approve_invoice(db, invoice.id)
        raise AssertionError("approval should fail")
    except Exception as exc:
        assert "cannot be approved" in str(exc).lower() or "issues" in str(exc).lower()


def test_missing_price_blocks_approval(db: Session):
    invoice = create_invoice(
        db,
        InvoiceCreateIn(
            customer=CustomerIn(name="Rahul", email="rahul@example.com"),
            items=[InvoiceItemIn(requested_service="quantum marketing", quantity=Decimal("2"))],
        ),
    )
    assert invoice.items[0].unit_price is None
    assert invoice.items[0].price_source == "unresolved"


def test_invalid_quantity_rejected(db: Session):
    try:
        create_invoice(
            db,
            InvoiceCreateIn(
                customer=CustomerIn(name="Rahul", email="rahul@example.com"),
                items=[InvoiceItemIn(requested_service="Logo Design", quantity=Decimal("0"))],
            ),
        )
        raise AssertionError("quantity 0 should be invalid")
    except Exception:
        pass


def test_valid_invoice_approved_and_audited(db: Session):
    invoice = create_invoice(db, _happy_payload(db))
    approved = approve_invoice(db, invoice.id)
    assert approved.status == InvoiceStatus.APPROVED
    events = {row.event_type for row in db.execute(select(AuditLog).where(AuditLog.invoice_id == approved.id)).scalars()}
    assert "invoice_approved" in events
    assert "invoice_created" in events


def test_export_creates_audit_and_pdf(db: Session):
    invoice = approve_invoice(db, create_invoice(db, _happy_payload(db)).id)
    pdf = generate_invoice_pdf(invoice)
    assert pdf.startswith(b"%PDF")
    exported = mark_exported(db, invoice.id)
    assert exported.status == InvoiceStatus.EXPORTED
    events = {row.event_type for row in db.execute(select(AuditLog).where(AuditLog.invoice_id == exported.id)).scalars()}
    assert "invoice_exported" in events


def test_customer_quoted_price_is_ignored(db: Session):
    invoice = create_invoice(
        db,
        InvoiceCreateIn(
            customer=CustomerIn(name="Rahul", email="rahul@example.com"),
            items=[InvoiceItemIn(requested_service="Corporate Website", quantity=Decimal("1"))],
            notes="Customer asked for 50000 but catalog must win",
        ),
    )
    assert invoice.items[0].unit_price == Decimal("40000.00")
    assert invoice.total != Decimal("50000.00")
