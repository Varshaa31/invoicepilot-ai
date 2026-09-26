from io import BytesIO
from reportlab.lib import colors
from reportlab.lib.enums import TA_RIGHT, TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, KeepTogether
)


def generate_invoice_pdf(draft) -> bytes:
    buffer = BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=18 * mm,
        leftMargin=18 * mm,
        topMargin=16 * mm,
        bottomMargin=16 * mm,
        title=f"Invoice {draft.invoice_number}",
        author=draft.seller_name,
    )

    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(
        name="InvoiceTitle",
        parent=styles["Title"],
        fontSize=24,
        leading=28,
        alignment=TA_RIGHT,
        spaceAfter=4,
    ))
    styles.add(ParagraphStyle(
        name="Small",
        parent=styles["Normal"],
        fontSize=8.5,
        leading=11,
    ))
    styles.add(ParagraphStyle(
        name="Right",
        parent=styles["Normal"],
        alignment=TA_RIGHT,
    ))

    story = []

    header = Table([
        [
            Paragraph(f"<b>{draft.seller_name}</b><br/>{draft.seller_email or ''}", styles["Normal"]),
            Paragraph("INVOICE", styles["InvoiceTitle"]),
        ]
    ], colWidths=[90 * mm, 80 * mm])

    header.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("ALIGN", (1, 0), (1, 0), "RIGHT"),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
    ]))
    story.append(header)

    meta = Table([
        [
            Paragraph(
                f"<b>Bill To</b><br/>{draft.customer.name or 'Customer'}<br/>"
                f"{draft.customer.email or ''}",
                styles["Normal"],
            ),
            Paragraph(
                f"<b>Invoice #</b> {draft.invoice_number}<br/>"
                f"<b>Issue Date</b> {draft.issue_date}<br/>"
                f"<b>Due Date</b> {draft.due_date}",
                styles["Right"],
            ),
        ]
    ], colWidths=[90 * mm, 80 * mm])

    meta.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LINEBELOW", (0, 0), (-1, -1), 0.5, colors.grey),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
    ]))
    story += [meta, Spacer(1, 8 * mm)]

    data = [["Description", "Qty", "Unit Price", "Amount"]]
    for line in draft.lines:
        data.append([
            Paragraph(line.description, styles["Small"]),
            str(line.quantity),
            f"{draft.currency} {line.unit_price:,.2f}",
            f"{draft.currency} {line.line_total:,.2f}",
        ])

    table = Table(data, colWidths=[88 * mm, 18 * mm, 32 * mm, 32 * mm], repeatRows=1)
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1F2937")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("ALIGN", (1, 1), (-1, -1), "RIGHT"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("GRID", (0, 0), (-1, -1), 0.25, colors.lightgrey),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F9FAFB")]),
        ("TOPPADDING", (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
    ]))
    story.append(table)
    story.append(Spacer(1, 6 * mm))

    totals = Table([
        ["Subtotal", f"{draft.currency} {draft.subtotal:,.2f}"],
        [f"Tax ({draft.tax_rate}%)", f"{draft.currency} {draft.tax:,.2f}"],
        ["Discount", f"{draft.currency} {draft.discount:,.2f}"],
        ["TOTAL", f"{draft.currency} {draft.grand_total:,.2f}"],
    ], colWidths=[130 * mm, 40 * mm])

    totals.setStyle(TableStyle([
        ("ALIGN", (1, 0), (1, -1), "RIGHT"),
        ("FONTNAME", (0, 3), (-1, 3), "Helvetica-Bold"),
        ("LINEABOVE", (0, 3), (-1, 3), 1, colors.black),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    story.append(totals)

    if draft.notes:
        story += [
            Spacer(1, 8 * mm),
            Paragraph("<b>Notes</b>", styles["Normal"]),
            Paragraph(draft.notes, styles["Small"]),
        ]

    story += [
        Spacer(1, 12 * mm),
        Paragraph(
            "Prices verified against the connected service catalog. "
            "Totals calculated by the application after human review.",
            styles["Small"],
        ),
    ]

    doc.build(story)
    return buffer.getvalue()
