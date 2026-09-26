from decimal import Decimal, ROUND_HALF_UP

CENT = Decimal("0.01")
QUANTITY_QUANTUM = Decimal("0.01")


def to_decimal(value) -> Decimal:
    if isinstance(value, Decimal):
        return value
    return Decimal(str(value))


def money(value) -> Decimal:
    return to_decimal(value).quantize(CENT, rounding=ROUND_HALF_UP)


def quantity_value(value) -> Decimal:
    qty = to_decimal(value).quantize(QUANTITY_QUANTUM, rounding=ROUND_HALF_UP)
    if qty <= 0:
        raise ValueError("Quantity must be greater than zero.")
    return qty
