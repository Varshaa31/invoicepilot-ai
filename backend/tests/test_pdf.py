from app.core.exceptions import ConflictError
from app.models.entities import InvoiceStatus
from app.schemas.common import CustomerIn, InvoiceCreateIn, InvoiceItemIn
from app.services.invoices import create_invoice
from app.services.pdf import generate_invoice_pdf


def test_pdf_rejected_before_approval(db):
    invoice = create_invoice(
        db,
        InvoiceCreateIn(
            customer=CustomerIn(name="Rahul", email="rahul@example.com"),
            items=[InvoiceItemIn(requested_service="Logo Design", quantity=1)],
        ),
    )
    assert invoice.status != InvoiceStatus.APPROVED
    try:
        generate_invoice_pdf(invoice)
        raise AssertionError("unapproved PDF should fail")
    except ConflictError:
        pass
