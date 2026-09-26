import streamlit as st
from datetime import date, timedelta
from decimal import Decimal, InvalidOperation

from models import InvoiceRequest, InvoiceDraft, InvoiceLine, Customer
from ai_extractor import extract_invoice_request
from pricing import PriceCatalog
from invoice import calculate_invoice, invoice_to_dataframe
from pdf_generator import generate_invoice_pdf

st.set_page_config(
    page_title="InvoicePilot AI",
    page_icon="🧾",
    layout="wide",
)

CATALOG_PATH = "data/services.csv"

@st.cache_resource
def get_catalog():
    return PriceCatalog(CATALOG_PATH)

catalog = get_catalog()

if "request" not in st.session_state:
    st.session_state.request = None
if "draft" not in st.session_state:
    st.session_state.draft = None
if "approved" not in st.session_state:
    st.session_state.approved = False
if "pdf_bytes" not in st.session_state:
    st.session_state.pdf_bytes = None

st.title("🧾 InvoicePilot AI")
st.caption("AI-assisted invoice automation: extract → verify prices → calculate → review → approve")

with st.sidebar:
    st.header("Configuration")
    tax_rate = st.number_input("Tax rate (%)", min_value=0.0, max_value=100.0, value=18.0, step=0.5)
    currency = st.selectbox("Currency", ["INR", "USD", "EUR"], index=0)
    st.divider()
    st.subheader("Service Catalog")
    st.write(f"{len(catalog.services)} services loaded")
    st.caption("Prices always come from the catalog. The AI never invents prices.")

st.subheader("1. Customer requirement")
default_text = (
    "Hi, I'm Priya from Acme Labs. Please invoice us for 3 landing pages "
    "and 2 logo designs. Send it to priya@acme.com. This is for our product launch."
)
customer_message = st.text_area(
    "Paste the customer's message",
    value=default_text,
    height=160,
    placeholder="Example: We need 5 social media campaigns for Rahul at rahul@example.com.",
)

col1, col2 = st.columns([1, 1])
with col1:
    extract_clicked = st.button("🤖 Extract requirement", type="primary", use_container_width=True)
with col2:
    if st.button("Reset", use_container_width=True):
        for key in ["request", "draft", "approved", "pdf_bytes"]:
            st.session_state[key] = None
        st.rerun()

if extract_clicked:
    if not customer_message.strip():
        st.error("Enter a customer requirement first.")
    else:
        with st.spinner("Extracting structured requirements..."):
            try:
                st.session_state.request = extract_invoice_request(customer_message)
                st.session_state.draft = None
                st.session_state.approved = False
                st.session_state.pdf_bytes = None
            except Exception as e:
                st.error(f"Extraction failed: {e}")

request = st.session_state.request

if request:
    st.divider()
    st.subheader("2. AI extraction")

    c1, c2 = st.columns(2)
    with c1:
        st.markdown("**Customer**")
        st.write(f"Name: {request.customer.name or 'Missing'}")
        st.write(f"Email: {request.customer.email or 'Missing'}")
    with c2:
        st.markdown("**AI notes**")
        if request.missing_information:
            st.warning("Missing: " + ", ".join(request.missing_information))
        else:
            st.success("No required information is missing.")
        if request.ambiguous_items:
            st.warning("Ambiguous: " + ", ".join(request.ambiguous_items))
        if request.notes:
            st.info(request.notes)

    st.markdown("**Requested services**")
    extracted_rows = []
    for item in request.items:
        extracted_rows.append({
            "Requested service": item.requested_service,
            "Quantity": item.quantity if item.quantity is not None else "",
            "Notes": item.notes or "",
        })
    st.dataframe(extracted_rows, use_container_width=True, hide_index=True)

    st.divider()
    st.subheader("3. Resolve services & verify catalog prices")

    resolved_lines = []
    blocked = bool(request.missing_information)

    for idx, item in enumerate(request.items):
        result = catalog.resolve(item.requested_service)

        st.markdown(f"**Item {idx + 1}: {item.requested_service}**")

        if result.status == "MATCHED":
            quantity = item.quantity or 0
            if quantity <= 0:
                st.warning("Quantity is missing or invalid. Set it below.")
                blocked = True

            unit_price = result.match["unit_price"]
            st.success(
                f"✓ Matched to **{result.match['service_name']}** · "
                f"{catalog.format_money(unit_price, currency)} / unit · "
                f"Catalog ID `{result.match['service_id']}`"
            )

            edited_qty = st.number_input(
                "Quantity",
                min_value=1,
                value=max(1, quantity),
                step=1,
                key=f"qty_{idx}",
            )
            resolved_lines.append(
                InvoiceLine(
                    service_id=result.match["service_id"],
                    description=result.match["service_name"],
                    quantity=edited_qty,
                    unit_price=Decimal(str(unit_price)),
                    notes=item.notes,
                )
            )

        elif result.status == "AMBIGUOUS":
            blocked = True
            st.warning("Multiple catalog matches found. Choose one before continuing.")
            options = result.options
            labels = [
                f"{x['service_name']} — {catalog.format_money(x['unit_price'], currency)}"
                for x in options
            ]
            choice = st.selectbox("Select service", labels, key=f"match_{idx}")
            selected = options[labels.index(choice)]
            if st.button(f"Use {selected['service_name']}", key=f"use_{idx}"):
                st.session_state[f"override_{idx}"] = selected

            if f"override_{idx}" in st.session_state:
                chosen = st.session_state[f"override_{idx}"]
                qty = item.quantity or 1
                resolved_lines.append(
                    InvoiceLine(
                        service_id=chosen["service_id"],
                        description=chosen["service_name"],
                        quantity=qty,
                        unit_price=Decimal(str(chosen["unit_price"])),
                        notes=item.notes,
                    )
                )
                blocked = False

        else:
            blocked = True
            st.error(
                f"Price unavailable for `{item.requested_service}`. "
                "No price will be fabricated."
            )
            st.caption("Add the service to the catalog or edit the customer requirement.")

    st.divider()
    st.subheader("4. Invoice details")

    left, right = st.columns(2)
    with left:
        invoice_number = st.text_input("Invoice number", value=f"INV-{date.today().strftime('%Y%m%d')}-001")
        company_name = st.text_input("Seller name", value="InvoicePilot AI")
        company_email = st.text_input("Seller email", value="billing@invoicepilot.demo")
    with right:
        due_date = st.date_input("Due date", value=date.today() + timedelta(days=7))
        notes = st.text_area("Invoice notes", value=request.notes or "Thank you for your business.", height=90)

    if resolved_lines and not blocked:
        draft = InvoiceDraft(
            invoice_number=invoice_number,
            issue_date=date.today(),
            due_date=due_date,
            seller_name=company_name,
            seller_email=company_email,
            customer=request.customer,
            lines=resolved_lines,
            tax_rate=Decimal(str(tax_rate)),
            currency=currency,
            notes=notes,
        )
        draft = calculate_invoice(draft)
        st.session_state.draft = draft
        st.session_state.approved = False
        st.session_state.pdf_bytes = None

    draft = st.session_state.draft

    if draft:
        st.divider()
        st.subheader("5. Review & approval")

        status_col, total_col = st.columns([2, 1])
        with status_col:
            st.success("✓ Customer identified")
            st.success("✓ Services matched to catalog")
            st.success("✓ Prices verified from catalog")
            st.success("✓ Totals calculated deterministically")
        with total_col:
            st.metric("Grand Total", f"{draft.currency} {draft.grand_total:,.2f}")

        st.dataframe(
            invoice_to_dataframe(draft),
            use_container_width=True,
            hide_index=True,
        )

        totals = st.columns(4)
        totals[0].metric("Subtotal", f"{draft.currency} {draft.subtotal:,.2f}")
        totals[1].metric(f"Tax ({draft.tax_rate}%)", f"{draft.currency} {draft.tax:,.2f}")
        totals[2].metric("Discount", f"{draft.currency} {draft.discount:,.2f}")
        totals[3].metric("Total", f"{draft.currency} {draft.grand_total:,.2f}")

        approve = st.checkbox(
            "I have reviewed the customer, services, prices, and totals.",
            value=st.session_state.approved,
        )

        if st.button("✅ Approve & Generate PDF", type="primary", disabled=not approve):
            with st.spinner("Generating professional invoice PDF..."):
                st.session_state.approved = True
                st.session_state.pdf_bytes = generate_invoice_pdf(draft)

        if st.session_state.pdf_bytes:
            st.success("Invoice approved and PDF generated.")
            st.download_button(
                "⬇️ Download Invoice PDF",
                data=st.session_state.pdf_bytes,
                file_name=f"{draft.invoice_number}.pdf",
                mime="application/pdf",
                use_container_width=True,
            )
    else:
        if blocked:
            st.warning("Resolve missing or ambiguous information before generating the invoice.")
        elif not resolved_lines:
            st.info("Resolve at least one catalog-backed service to continue.")
