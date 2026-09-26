from datetime import date
from decimal import Decimal
from models import InvoiceDraft, InvoiceLine, Customer
from invoice import calculate_invoice


def test_invoice_math():
    draft = InvoiceDraft(
        invoice_number="TEST-001",
        issue_date=date.today(),
        due_date=date.today(),
        seller_name="Test Seller",
        customer=Customer(name="Alice", email="alice@example.com"),
        lines=[
            InvoiceLine(
                service_id="X",
                description="Test",
                quantity=2,
                unit_price=Decimal("1000"),
            )
        ],
        tax_rate=Decimal("18"),
        currency="INR",
    )

    result = calculate_invoice(draft)
    assert result.subtotal == Decimal("2000.00")
    assert result.tax == Decimal("360.00")
    assert result.grand_total == Decimal("2360.00")
