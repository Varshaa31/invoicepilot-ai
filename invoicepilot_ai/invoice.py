from decimal import Decimal, ROUND_HALF_UP
import pandas as pd
from models import InvoiceDraft


CENT = Decimal("0.01")


def money(value: Decimal) -> Decimal:
    return Decimal(value).quantize(CENT, rounding=ROUND_HALF_UP)


def calculate_invoice(draft: InvoiceDraft) -> InvoiceDraft:
    subtotal = Decimal("0")

    for line in draft.lines:
        line.line_total = money(line.unit_price * line.quantity)
        subtotal += line.line_total

    subtotal = money(subtotal)
    tax = money((subtotal - draft.discount) * draft.tax_rate / Decimal("100"))
    taxable = max(Decimal("0"), subtotal - draft.discount)
    tax = money(taxable * draft.tax_rate / Decimal("100"))
    total = money(taxable + tax)

    draft.subtotal = subtotal
    draft.tax = tax
    draft.grand_total = total

    return draft


def invoice_to_dataframe(draft: InvoiceDraft) -> pd.DataFrame:
    return pd.DataFrame([
        {
            "Service": line.description,
            "Qty": line.quantity,
            "Unit Price": f"{draft.currency} {line.unit_price:,.2f}",
            "Amount": f"{draft.currency} {line.line_total:,.2f}",
            "Catalog ID": line.service_id,
        }
        for line in draft.lines
    ])
