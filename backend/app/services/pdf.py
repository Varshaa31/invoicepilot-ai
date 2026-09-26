from datetime import datetime
from io import BytesIO
from pathlib import Path
from typing import Optional
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from app.core.config import get_settings
from app.core.exceptions import ConflictError
from app.models.entities import Invoice, InvoiceStatus


# ----------------------------------------------------------------------
# Invoice colors
# ----------------------------------------------------------------------

NAVY = colors.HexColor("#12263A")
GOLD = colors.HexColor("#C4A35A")
IVORY = colors.HexColor("#F7F4EE")
SLATE = colors.HexColor("#5B6573")
LIGHT_BORDER = colors.HexColor("#E5E0D6")
WHITE = colors.white

APPROVED_BG = colors.HexColor("#E8F5EC")
APPROVED_TEXT = colors.HexColor("#247A43")

EXPORTED_BG = colors.HexColor("#EEF2FF")
EXPORTED_TEXT = colors.HexColor("#4057A6")


# ----------------------------------------------------------------------
# Font configuration
# ----------------------------------------------------------------------

FONT_REGULAR = "InvoicePilot-Regular"
FONT_BOLD = "InvoicePilot-Bold"


def _find_font(
    filenames: list[str],
) -> Optional[Path]:
    """
    Find a Unicode-capable font.

    DejaVu Sans and Noto Sans support the Indian Rupee symbol.
    """

    possible_directories = [
        Path("/usr/share/fonts/truetype/dejavu"),
        Path("/usr/share/fonts/truetype/noto"),
        Path("/usr/share/fonts/opentype/noto"),
        Path("/usr/local/share/fonts"),
        Path.home() / ".fonts",
        Path(r"C:\Windows\Fonts"),
    ]

    for directory in possible_directories:
        if not directory.exists():
            continue

        for filename in filenames:
            path = directory / filename

            if path.exists():
                return path

    return None


def _register_invoice_fonts() -> tuple[str, str, bool]:
    """
    Register a Unicode-capable regular/bold font pair.

    Returns:
        regular font name,
        bold font name,
        whether the font supports the ₹ symbol
    """

    regular_path = _find_font(
        [
            "DejaVuSans.ttf",
            "NotoSans-Regular.ttf",
        ]
    )

    bold_path = _find_font(
        [
            "DejaVuSans-Bold.ttf",
            "NotoSans-Bold.ttf",
        ]
    )

    if regular_path and bold_path:
        try:
            if FONT_REGULAR not in pdfmetrics.getRegisteredFontNames():
                pdfmetrics.registerFont(
                    TTFont(
                        FONT_REGULAR,
                        str(regular_path),
                    )
                )

            if FONT_BOLD not in pdfmetrics.getRegisteredFontNames():
                pdfmetrics.registerFont(
                    TTFont(
                        FONT_BOLD,
                        str(bold_path),
                    )
                )

            try:
                pdfmetrics.registerFontFamily(
                    "InvoicePilot",
                    normal=FONT_REGULAR,
                    bold=FONT_BOLD,
                )
            except Exception:
                pass

            return FONT_REGULAR, FONT_BOLD, True

        except Exception:
            pass

    return "Helvetica", "Helvetica-Bold", False


# ----------------------------------------------------------------------
# Money formatting
# ----------------------------------------------------------------------

def _money(
    invoice: Invoice,
    value,
    supports_rupee: bool,
) -> str:
    """
    Format money using the currency stored on the invoice.

    Important:
    This uses invoice.currency, not the current workspace setting.
    """

    amount = f"{value:,.2f}"

    if invoice.currency == "INR":
        if supports_rupee:
            return f"₹{amount}"

        return f"INR {amount}"

    if invoice.currency == "USD":
        return f"${amount}"

    if invoice.currency == "EUR":
        return f"€{amount}"

    if invoice.currency == "GBP":
        return f"£{amount}"

    return f"{invoice.currency} {amount}"


# ----------------------------------------------------------------------
# Status presentation
# ----------------------------------------------------------------------

def _status_presentation(
    status: InvoiceStatus,
) -> tuple[str, colors.Color, colors.Color]:
    """
    Return a customer-friendly status label and its colors.
    """

    if status == InvoiceStatus.APPROVED:
        return (
            "Approved",
            APPROVED_BG,
            APPROVED_TEXT,
        )

    if status == InvoiceStatus.EXPORTED:
        return (
            "Exported",
            EXPORTED_BG,
            EXPORTED_TEXT,
        )

    return (
        status.value.replace("_", " ").title(),
        IVORY,
        NAVY,
    )


# ----------------------------------------------------------------------
# Invoice settings helpers
# ----------------------------------------------------------------------

def _invoice_business_details(invoice: Invoice):
    """
    Get business/payment information from the invoice snapshot.

    Newer invoices contain snapshots of workspace settings taken when
    the invoice was created.

    Older invoices safely fall back to application configuration.

    This is intentional: historical invoices should not unexpectedly
    break if they were created before the snapshot migration existed.
    """

    settings = get_settings()

    company_name = (
        getattr(invoice, "company_name_snapshot", None)
        or settings.company_name
    )

    company_email = (
        getattr(invoice, "company_email_snapshot", None)
        or settings.company_email
    )

    company_address = (
        getattr(invoice, "company_address_snapshot", None)
        or settings.company_address
    )

    payment_information = (
        getattr(invoice, "payment_information_snapshot", None)
        or settings.company_payment_info
    )

    tax_enabled = getattr(
        invoice,
        "tax_enabled_snapshot",
        None,
    )

    tax_type = getattr(
        invoice,
        "tax_type_snapshot",
        None,
    )

    gstin = getattr(
        invoice,
        "gstin_snapshot",
        None,
    )

    business_state = getattr(
        invoice,
        "business_state_snapshot",
        None,
    )

    return (
        company_name,
        company_email,
        company_address,
        payment_information,
        tax_enabled,
        tax_type,
        gstin,
        business_state,
        settings,
    )


# ----------------------------------------------------------------------
# PDF generation
# ----------------------------------------------------------------------

def generate_invoice_pdf(invoice: Invoice) -> bytes:
    """
    Generate a customer-facing PDF invoice.

    PDF export is allowed only for approved/exported invoices.

    Important design rules:

    1. Business identity comes from the invoice snapshot.
    2. Payment information comes from the invoice snapshot.
    3. Tax configuration shown on the invoice comes from the snapshot.
    4. Currency comes from the invoice.
    5. Subtotal, tax amount and total come from the invoice.
    6. The current workspace settings are NOT used to recalculate
       historical invoice values.
    """

    if invoice.status not in {
        InvoiceStatus.APPROVED,
        InvoiceStatus.EXPORTED,
    }:
        raise ConflictError(
            "PDF can only be generated from an approved invoice."
        )

    (
        company_name_value,
        company_email_value,
        company_address_value,
        payment_information_value,
        tax_enabled_snapshot,
        tax_type_snapshot,
        gstin_snapshot,
        business_state_snapshot,
        settings,
    ) = _invoice_business_details(invoice)

    regular_font, bold_font, supports_rupee = (
        _register_invoice_fonts()
    )

    buffer = BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=16 * mm,
        leftMargin=16 * mm,
        topMargin=14 * mm,
        bottomMargin=30 * mm,
        title=f"Invoice {invoice.invoice_number}",
        author=company_name_value,
        subject="Business Invoice",
    )

    styles = getSampleStyleSheet()

    # ------------------------------------------------------------------
    # Styles
    # ------------------------------------------------------------------

    styles.add(
        ParagraphStyle(
            name="InvoiceBrand",
            parent=styles["Title"],
            fontName=bold_font,
            fontSize=22,
            leading=25,
            textColor=NAVY,
            alignment=TA_RIGHT,
            spaceAfter=0,
        )
    )

    styles.add(
        ParagraphStyle(
            name="InvoiceNormal",
            parent=styles["Normal"],
            fontName=regular_font,
            fontSize=9,
            leading=12,
            textColor=colors.black,
        )
    )

    styles.add(
        ParagraphStyle(
            name="InvoiceNormalBold",
            parent=styles["Normal"],
            fontName=bold_font,
            fontSize=9,
            leading=12,
            textColor=colors.black,
        )
    )

    styles.add(
        ParagraphStyle(
            name="InvoiceMuted",
            parent=styles["Normal"],
            fontName=regular_font,
            fontSize=8.5,
            leading=11,
            textColor=SLATE,
        )
    )

    styles.add(
        ParagraphStyle(
            name="InvoiceSmall",
            parent=styles["Normal"],
            fontName=regular_font,
            fontSize=8.5,
            leading=11,
            textColor=NAVY,
        )
    )

    styles.add(
        ParagraphStyle(
            name="InvoiceRight",
            parent=styles["Normal"],
            fontName=regular_font,
            fontSize=9,
            leading=13,
            alignment=TA_RIGHT,
            textColor=colors.black,
        )
    )

    styles.add(
        ParagraphStyle(
            name="InvoiceRightBold",
            parent=styles["Normal"],
            fontName=bold_font,
            fontSize=9,
            leading=13,
            alignment=TA_RIGHT,
            textColor=colors.black,
        )
    )

    styles.add(
        ParagraphStyle(
            name="InvoiceMetaLabel",
            parent=styles["Normal"],
            fontName=regular_font,
            fontSize=8,
            leading=11,
            textColor=SLATE,
            alignment=TA_RIGHT,
        )
    )

    styles.add(
        ParagraphStyle(
            name="InvoiceMetaValue",
            parent=styles["Normal"],
            fontName=bold_font,
            fontSize=9,
            leading=12,
            textColor=NAVY,
            alignment=TA_RIGHT,
        )
    )

    styles.add(
        ParagraphStyle(
            name="Footer",
            parent=styles["Normal"],
            fontName=regular_font,
            fontSize=7.2,
            leading=10,
            textColor=SLATE,
            alignment=TA_CENTER,
        )
    )

    styles.add(
        ParagraphStyle(
            name="FooterBold",
            parent=styles["Normal"],
            fontName=bold_font,
            fontSize=7.5,
            leading=10,
            textColor=SLATE,
            alignment=TA_CENTER,
        )
    )

    styles.add(
        ParagraphStyle(
            name="TaxDetails",
            parent=styles["Normal"],
            fontName=regular_font,
            fontSize=8,
            leading=10,
            textColor=SLATE,
        )
    )

    story = []

    customer = invoice.customer

    issued = (
        invoice.created_at.strftime("%d %b %Y")
        if invoice.created_at
        else ""
    )

    # ------------------------------------------------------------------
    # Header
    # ------------------------------------------------------------------

    company_name = escape(str(company_name_value or ""))
    company_email = escape(str(company_email_value or ""))
    company_address = escape(str(company_address_value or ""))

    company_header = (
        f"<b>{company_name}</b><br/>"
        f"{company_email}<br/>"
        f"{company_address}"
    )

    header = Table(
        [
            [
                Paragraph(
                    company_header,
                    styles["InvoiceNormal"],
                ),
                Paragraph(
                    "INVOICE",
                    styles["InvoiceBrand"],
                ),
            ]
        ],
        colWidths=[
            100 * mm,
            75 * mm,
        ],
    )

    header.setStyle(
        TableStyle(
            [
                (
                    "VALIGN",
                    (0, 0),
                    (-1, -1),
                    "TOP",
                ),
                (
                    "BACKGROUND",
                    (0, 0),
                    (-1, -1),
                    IVORY,
                ),
                (
                    "LEFTPADDING",
                    (0, 0),
                    (-1, -1),
                    10,
                ),
                (
                    "RIGHTPADDING",
                    (0, 0),
                    (-1, -1),
                    10,
                ),
                (
                    "TOPPADDING",
                    (0, 0),
                    (-1, -1),
                    10,
                ),
                (
                    "BOTTOMPADDING",
                    (0, 0),
                    (-1, -1),
                    10,
                ),
                (
                    "BOX",
                    (0, 0),
                    (-1, -1),
                    0.6,
                    GOLD,
                ),
            ]
        )
    )

    story += [
        header,
        Spacer(1, 8 * mm),
    ]

    # ------------------------------------------------------------------
    # Bill To + Invoice Information
    # ------------------------------------------------------------------

    customer_name = (
        customer.name
        if customer and customer.name
        else "Customer"
    )

    customer_company = (
        customer.company
        if customer and customer.company
        else ""
    )

    customer_email = (
        customer.email
        if customer and customer.email
        else ""
    )

    customer_phone = (
        customer.phone
        if customer and customer.phone
        else ""
    )

    customer_address = (
        customer.address
        if customer and customer.address
        else ""
    )

    customer_name = escape(str(customer_name))
    customer_company = escape(str(customer_company))
    customer_email = escape(str(customer_email))
    customer_phone = escape(str(customer_phone))
    customer_address = escape(str(customer_address))

    bill_to_parts = [
        "<b>Bill To</b>",
        customer_name,
    ]

    if customer_company:
        bill_to_parts.append(customer_company)

    if customer_email:
        bill_to_parts.append(customer_email)

    if customer_phone:
        bill_to_parts.append(customer_phone)

    if customer_address:
        bill_to_parts.append(
            customer_address.replace(
                "\n",
                "<br/>",
            )
        )

    bill_to = "<br/>".join(bill_to_parts)

    # ------------------------------------------------------------------
    # Status badge
    # ------------------------------------------------------------------

    status_label, status_bg, status_text = (
        _status_presentation(invoice.status)
    )

    status_badge = Table(
        [
            [
                Paragraph(
                    f"<b>✓ {status_label}</b>",
                    ParagraphStyle(
                        "StatusBadge",
                        parent=styles["InvoiceNormal"],
                        fontName=bold_font,
                        fontSize=8,
                        leading=10,
                        textColor=status_text,
                        alignment=TA_CENTER,
                    ),
                )
            ]
        ],
        colWidths=[30 * mm],
    )

    status_badge.setStyle(
        TableStyle(
            [
                (
                    "BACKGROUND",
                    (0, 0),
                    (-1, -1),
                    status_bg,
                ),
                (
                    "BOX",
                    (0, 0),
                    (-1, -1),
                    0.4,
                    status_bg,
                ),
                (
                    "TOPPADDING",
                    (0, 0),
                    (-1, -1),
                    4,
                ),
                (
                    "BOTTOMPADDING",
                    (0, 0),
                    (-1, -1),
                    4,
                ),
                (
                    "LEFTPADDING",
                    (0, 0),
                    (-1, -1),
                    6,
                ),
                (
                    "RIGHTPADDING",
                    (0, 0),
                    (-1, -1),
                    6,
                ),
            ]
        )
    )

    invoice_number = escape(str(invoice.invoice_number))
    currency = escape(str(invoice.currency))

    invoice_details_rows = [
        [
            Paragraph(
                "Invoice Number",
                styles["InvoiceMetaLabel"],
            ),
            Paragraph(
                f"#{invoice_number}",
                styles["InvoiceMetaValue"],
            ),
        ],
        [
            Paragraph(
                "Date",
                styles["InvoiceMetaLabel"],
            ),
            Paragraph(
                issued,
                styles["InvoiceMetaValue"],
            ),
        ],
        [
            Paragraph(
                "Status",
                styles["InvoiceMetaLabel"],
            ),
            status_badge,
        ],
        [
            Paragraph(
                "Currency",
                styles["InvoiceMetaLabel"],
            ),
            Paragraph(
                currency,
                styles["InvoiceMetaValue"],
            ),
        ],
    ]

    invoice_details = Table(
        invoice_details_rows,
        colWidths=[
            35 * mm,
            40 * mm,
        ],
    )

    invoice_details.setStyle(
        TableStyle(
            [
                (
                    "VALIGN",
                    (0, 0),
                    (-1, -1),
                    "MIDDLE",
                ),
                (
                    "ALIGN",
                    (0, 0),
                    (-1, -1),
                    "RIGHT",
                ),
                (
                    "LEFTPADDING",
                    (0, 0),
                    (-1, -1),
                    0,
                ),
                (
                    "RIGHTPADDING",
                    (0, 0),
                    (-1, -1),
                    0,
                ),
                (
                    "TOPPADDING",
                    (0, 0),
                    (-1, -1),
                    3,
                ),
                (
                    "BOTTOMPADDING",
                    (0, 0),
                    (-1, -1),
                    3,
                ),
            ]
        )
    )

    meta_table = Table(
        [
            [
                Paragraph(
                    bill_to,
                    styles["InvoiceNormal"],
                ),
                invoice_details,
            ]
        ],
        colWidths=[
            100 * mm,
            75 * mm,
        ],
    )

    meta_table.setStyle(
        TableStyle(
            [
                (
                    "VALIGN",
                    (0, 0),
                    (-1, -1),
                    "TOP",
                ),
                (
                    "LEFTPADDING",
                    (0, 0),
                    (-1, -1),
                    0,
                ),
                (
                    "RIGHTPADDING",
                    (0, 0),
                    (-1, -1),
                    0,
                ),
                (
                    "TOPPADDING",
                    (0, 0),
                    (-1, -1),
                    0,
                ),
                (
                    "BOTTOMPADDING",
                    (0, 0),
                    (-1, -1),
                    0,
                ),
            ]
        )
    )

    story += [
        meta_table,
        Spacer(1, 8 * mm),
    ]

    # ------------------------------------------------------------------
    # Line Items
    # ------------------------------------------------------------------

    data = [
        [
            "Service",
            "Qty",
            "Unit Price",
            "Amount",
        ]
    ]

    for item in invoice.items:
        service_name = escape(
            str(
                item.service_name_snapshot
                or item.requested_service
            )
        )

        data.append(
            [
                Paragraph(
                    f"<b>{service_name}</b><br/>"
                    f"<font color='#5B6573' size='8'>"
                    f"Price verified from Service Catalog"
                    f"</font>",
                    styles["InvoiceSmall"],
                ),
                Paragraph(
                    str(item.quantity),
                    styles["InvoiceRight"],
                ),
                Paragraph(
                    _money(
                        invoice,
                        item.unit_price or 0,
                        supports_rupee,
                    ),
                    styles["InvoiceRight"],
                ),
                Paragraph(
                    _money(
                        invoice,
                        item.line_total or 0,
                        supports_rupee,
                    ),
                    styles["InvoiceRight"],
                ),
            ]
        )

    table = Table(
        data,
        colWidths=[
            88 * mm,
            20 * mm,
            33 * mm,
            34 * mm,
        ],
        repeatRows=1,
    )

    table.setStyle(
        TableStyle(
            [
                (
                    "BACKGROUND",
                    (0, 0),
                    (-1, 0),
                    NAVY,
                ),
                (
                    "TEXTCOLOR",
                    (0, 0),
                    (-1, 0),
                    WHITE,
                ),
                (
                    "FONTNAME",
                    (0, 0),
                    (-1, 0),
                    bold_font,
                ),
                (
                    "FONTSIZE",
                    (0, 0),
                    (-1, 0),
                    9,
                ),
                (
                    "ALIGN",
                    (1, 1),
                    (-1, -1),
                    "RIGHT",
                ),
                (
                    "VALIGN",
                    (0, 0),
                    (-1, -1),
                    "MIDDLE",
                ),
                (
                    "GRID",
                    (0, 0),
                    (-1, -1),
                    0.25,
                    LIGHT_BORDER,
                ),
                (
                    "ROWBACKGROUNDS",
                    (0, 1),
                    (-1, -1),
                    [
                        WHITE,
                        IVORY,
                    ],
                ),
                (
                    "TOPPADDING",
                    (0, 0),
                    (-1, -1),
                    8,
                ),
                (
                    "BOTTOMPADDING",
                    (0, 0),
                    (-1, -1),
                    8,
                ),
                (
                    "LEFTPADDING",
                    (0, 0),
                    (-1, -1),
                    8,
                ),
                (
                    "RIGHTPADDING",
                    (0, 0),
                    (-1, -1),
                    8,
                ),
            ]
        )
    )

    story += [
        table,
        Spacer(1, 6 * mm),
    ]

    # ------------------------------------------------------------------
    # Totals
    #
    # These values are historical invoice values.
    # They are NOT recalculated from current workspace settings.
    # ------------------------------------------------------------------

    subtotal_text = _money(
        invoice,
        invoice.subtotal,
        supports_rupee,
    )

    tax_text = _money(
        invoice,
        invoice.tax_amount,
        supports_rupee,
    )

    total_text = _money(
        invoice,
        invoice.total,
        supports_rupee,
    )

    tax_rate = invoice.tax_rate or 0

    if tax_rate > 0:
        tax_label = f"Tax ({tax_rate}%)"
    else:
        tax_label = "Tax"

    totals = Table(
        [
            [
                "Subtotal",
                subtotal_text,
            ],
            [
                tax_label,
                tax_text,
            ],
            [
                "Grand Total",
                total_text,
            ],
        ],
        colWidths=[
            130 * mm,
            45 * mm,
        ],
    )

    totals.setStyle(
        TableStyle(
            [
                (
                    "FONTNAME",
                    (0, 0),
                    (-1, -1),
                    regular_font,
                ),
                (
                    "FONTSIZE",
                    (0, 0),
                    (-1, -1),
                    9,
                ),
                (
                    "ALIGN",
                    (1, 0),
                    (1, -1),
                    "RIGHT",
                ),
                (
                    "FONTNAME",
                    (0, 2),
                    (-1, 2),
                    bold_font,
                ),
                (
                    "TEXTCOLOR",
                    (0, 2),
                    (-1, 2),
                    NAVY,
                ),
                (
                    "BACKGROUND",
                    (0, 2),
                    (-1, 2),
                    GOLD,
                ),
                (
                    "LINEABOVE",
                    (0, 2),
                    (-1, 2),
                    0.6,
                    NAVY,
                ),
                (
                    "TOPPADDING",
                    (0, 0),
                    (-1, -1),
                    6,
                ),
                (
                    "BOTTOMPADDING",
                    (0, 0),
                    (-1, -1),
                    6,
                ),
                (
                    "LEFTPADDING",
                    (0, 0),
                    (-1, -1),
                    8,
                ),
                (
                    "RIGHTPADDING",
                    (0, 0),
                    (-1, -1),
                    8,
                ),
            ]
        )
    )

    story.append(totals)

    # ------------------------------------------------------------------
    # Tax / business information
    #
    # These values come from the invoice snapshots.
    # ------------------------------------------------------------------

    tax_details = []

    if tax_enabled_snapshot and tax_type_snapshot:
        tax_type_display = escape(str(tax_type_snapshot))

        tax_details.append(
            f"<b>Tax type:</b> {tax_type_display}"
        )

    if gstin_snapshot:
        tax_details.append(
            f"<b>GSTIN:</b> {escape(str(gstin_snapshot))}"
        )

    if business_state_snapshot:
        tax_details.append(
            f"<b>Business state:</b> "
            f"{escape(str(business_state_snapshot))}"
        )

    if tax_details:
        story += [
            Spacer(1, 4 * mm),
            Paragraph(
                "<br/>".join(tax_details),
                styles["TaxDetails"],
            ),
        ]

    # ------------------------------------------------------------------
    # Payment information
    #
    # This is business-owned information.
    # It does NOT come from the customer's message or AI extraction.
    # ------------------------------------------------------------------

    story += [
        Spacer(1, 9 * mm),
        Paragraph(
            "<b>Payment Information</b>",
            styles["InvoiceNormalBold"],
        ),
        Spacer(1, 1.5 * mm),
        Paragraph(
            escape(str(payment_information_value or "")),
            styles["InvoiceMuted"],
        ),
        Spacer(1, 5 * mm),
        Paragraph(
            "Prices are based on the selected services and verified "
            "before approval.",
            styles["InvoiceMuted"],
        ),
    ]

    # ------------------------------------------------------------------
    # Fixed footer
    #
    # Footer also uses invoice snapshots so changing workspace settings
    # later cannot rewrite an older invoice.
    # ------------------------------------------------------------------

    invoice_year = (
        invoice.created_at.year
        if invoice.created_at
        else datetime.now().year
    )

    footer_company = (
        f"{company_name_value} · "
        f"{company_address_value} · "
        f"{company_email_value}"
    )

    footer_terms = (
        "Please retain this invoice for your records. "
        f"For billing questions, contact {company_email_value}."
    )

    footer_copyright = (
        f"© {invoice_year} {company_name_value}. "
        "All rights reserved."
    )

    def draw_footer(canvas, document):
        canvas.saveState()

        page_width, _ = A4
        footer_y = 11 * mm

        # Footer divider
        canvas.setStrokeColor(LIGHT_BORDER)
        canvas.setLineWidth(0.5)

        canvas.line(
            16 * mm,
            footer_y + 14 * mm,
            page_width - 16 * mm,
            footer_y + 14 * mm,
        )

        # Company line
        canvas.setFillColor(SLATE)

        canvas.setFont(
            bold_font,
            7.5,
        )

        canvas.drawCentredString(
            page_width / 2,
            footer_y + 9 * mm,
            footer_company,
        )

        # Records / contact line
        canvas.setFont(
            regular_font,
            7,
        )

        canvas.drawCentredString(
            page_width / 2,
            footer_y + 5 * mm,
            footer_terms,
        )

        # Copyright
        canvas.drawCentredString(
            page_width / 2,
            footer_y + 1.5 * mm,
            footer_copyright,
        )

        canvas.restoreState()

    # ------------------------------------------------------------------
    # Build PDF
    # ------------------------------------------------------------------

    doc.build(
        story,
        onFirstPage=draw_footer,
        onLaterPages=draw_footer,
    )

    return buffer.getvalue()