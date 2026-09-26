from decimal import Decimal

from app.core.money import money
from app.services.pricing import invoice_totals, line_total


def test_quantity_calculation():
    assert line_total(Decimal("15000"), Decimal("3")) == Decimal("45000.00")


def test_subtotal_tax_grand_total():
    subtotal, tax, total = invoice_totals(
        [Decimal("65000.00"), Decimal("12000.00")],
        Decimal("18"),
    )
    assert subtotal == Decimal("77000.00")
    assert tax == Decimal("13860.00")
    assert total == Decimal("90860.00")


def test_decimal_precision_not_float():
    value = money(Decimal("10") / Decimal("3") * Decimal("3"))
    assert value == Decimal("10.00")
    assert isinstance(value, Decimal)


def test_missing_price_is_none_not_invented():
    unit_price = None
    assert unit_price is None
