from decimal import Decimal

from app.core.money import money, to_decimal


def line_total(unit_price: Decimal, quantity: Decimal) -> Decimal:
    return money(to_decimal(unit_price) * to_decimal(quantity))


def invoice_totals(line_totals: list[Decimal], tax_rate_percent: Decimal) -> tuple[Decimal, Decimal, Decimal]:
    subtotal = money(sum((to_decimal(value) for value in line_totals), Decimal("0")))
    tax_amount = money(subtotal * to_decimal(tax_rate_percent) / Decimal("100"))
    grand_total = money(subtotal + tax_amount)
    return subtotal, tax_amount, grand_total
