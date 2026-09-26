from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from uuid import UUID

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, selectinload

from app.core.exceptions import (
    AppError,
    ApprovalBlockedError,
    ConflictError,
    NotFoundError,
)
from app.core.money import money, quantity_value, to_decimal
from app.models.entities import (
    AuditLog,
    Customer,
    Invoice,
    InvoiceItem,
    InvoiceStatus,
    ResolutionStatus,
    Service,
    User,
)
from app.services.settings import get_or_create_settings
from app.schemas.common import (
    AuditLogOut,
    CustomerIn,
    CustomerOut,
    InvoiceCreateIn,
    InvoiceItemOut,
    InvoiceListOut,
    InvoiceOut,
    InvoiceUpdateIn,
    ServiceCandidateOut,
)
from app.services.audit import add_audit
from app.services.matching import (
    CatalogService,
    load_catalog,
    match_requested_item,
)
from app.services.pricing import invoice_totals, line_total


LOCKED_STATUSES = {
    InvoiceStatus.APPROVED,
    InvoiceStatus.EXPORTED,
}


def _now() -> datetime:
    return datetime.now(timezone.utc)


def generate_invoice_number(db: Session) -> str:
    today = datetime.now(timezone.utc).strftime("%Y%m%d")
    prefix = f"INV-{today}-"

    count = db.execute(
        select(func.count())
        .select_from(Invoice)
        .where(
            Invoice.invoice_number.startswith(prefix)
        )
    ).scalar_one()

    return f"{prefix}{int(count) + 1:03d}"


def get_invoice_or_404(
    db: Session,
    invoice_id: UUID,
    user: User,
) -> Invoice:
    invoice = db.execute(
        select(Invoice)
        .options(
            selectinload(Invoice.customer),
            selectinload(Invoice.items),
            selectinload(Invoice.audit_logs),
        )
        .where(
            Invoice.id == invoice_id,
            Invoice.user_id == user.id,
        )
    ).scalar_one_or_none()

    if invoice is None:
        raise NotFoundError("Invoice not found")

    return invoice


def upsert_customer(
    db: Session,
    payload: CustomerIn,
    user: User,
) -> Customer:
    customer = None

    if payload.email:
        customer = db.execute(
            select(Customer)
            .join(
                Invoice,
                Invoice.customer_id == Customer.id,
            )
            .where(
                Customer.email == str(payload.email),
                Invoice.user_id == user.id,
            )
            .limit(1)
        ).scalar_one_or_none()

    if customer is None:
        customer = Customer(
            name=payload.name,
            email=(
                str(payload.email)
                if payload.email
                else None
            ),
            phone=payload.phone,
            company=payload.company,
            address=payload.address,
        )

        db.add(customer)
        db.flush()

        return customer

    customer.name = payload.name
    customer.phone = payload.phone or customer.phone
    customer.company = payload.company or customer.company
    customer.address = payload.address or customer.address

    return customer


def _get_user_service(
    db: Session,
    service_id: UUID,
    user: User,
) -> Service:
    service = db.execute(
        select(Service).where(
            Service.id == service_id,
            Service.user_id == user.id,
        )
    ).scalar_one_or_none()

    if service is None or not service.active:
        raise NotFoundError(
            "Selected catalog service was not found."
        )

    return service


def _candidate_out(
    service: CatalogService,
    score: float | None = None,
) -> ServiceCandidateOut:
    return ServiceCandidateOut(
        service_id=service.id,
        name=service.name,
        description=service.description,
        unit_price=money(service.unit_price),
        currency=service.currency,
        match_score=score,
    )


def apply_match_to_item(
    item: InvoiceItem,
    requested: str,
    catalog: list[CatalogService],
    chosen: Service | None = None,
) -> None:
    item.requested_service = requested

    if chosen is not None:
        item.service_id = chosen.id
        item.service_name_snapshot = chosen.name
        item.unit_price = money(chosen.price)
        item.resolution_status = ResolutionStatus.MATCHED
        item.match_score = Decimal("1.0000")
        item.price_source = "service_catalog"
        item.line_total = line_total(
            item.unit_price,
            item.quantity,
        )
        return

    result = match_requested_item(
        requested,
        catalog,
    )

    item.match_score = Decimal(
        str(round(result.score, 4))
    )

    if (
        result.status == ResolutionStatus.MATCHED
        and result.match
    ):
        item.service_id = result.match.id
        item.service_name_snapshot = result.match.name
        item.unit_price = money(
            result.match.unit_price
        )
        item.resolution_status = ResolutionStatus.MATCHED
        item.price_source = "service_catalog"
        item.line_total = line_total(
            item.unit_price,
            item.quantity,
        )

    elif result.status == ResolutionStatus.AMBIGUOUS:
        item.service_id = None
        item.service_name_snapshot = None
        item.unit_price = None
        item.line_total = None
        item.resolution_status = ResolutionStatus.AMBIGUOUS
        item.price_source = "unresolved"

    else:
        item.service_id = None
        item.service_name_snapshot = None
        item.unit_price = None
        item.line_total = None
        item.resolution_status = ResolutionStatus.MISSING
        item.price_source = "unresolved"


def recalculate_invoice(invoice: Invoice) -> None:
    totals: list[Decimal] = []

    for item in invoice.items:
        if (
            item.resolution_status == ResolutionStatus.MATCHED
            and item.unit_price is not None
        ):
            item.line_total = line_total(
                item.unit_price,
                item.quantity,
            )
            totals.append(item.line_total)

        else:
            item.line_total = None

    subtotal, tax_amount, total = invoice_totals(
        totals,
        to_decimal(invoice.tax_rate),
    )

    invoice.subtotal = subtotal
    invoice.tax_amount = tax_amount
    invoice.total = total


def derive_status(
    invoice: Invoice,
) -> InvoiceStatus:
    if invoice.status in LOCKED_STATUSES:
        return invoice.status

    blockers = approval_blockers(invoice)

    if blockers:
        return InvoiceStatus.REVIEW_REQUIRED

    return InvoiceStatus.READY_FOR_APPROVAL


def approval_blockers(
    invoice: Invoice,
) -> list[str]:
    issues: list[str] = []

    customer = invoice.customer

    if not customer or not customer.name.strip():
        issues.append(
            "Customer name is required."
        )

    if not customer or not customer.email:
        issues.append(
            "Customer email is required."
        )

    if not invoice.items:
        issues.append(
            "Invoice needs at least one line item."
        )

    for index, item in enumerate(
        invoice.items,
        start=1,
    ):
        try:
            quantity_value(item.quantity)

        except ValueError:
            issues.append(
                f"Line {index} has an invalid quantity."
            )

        if (
            item.resolution_status
            == ResolutionStatus.AMBIGUOUS
        ):
            issues.append(
                f"'{item.requested_service}' is ambiguous. "
                "Choose a catalog service before approval."
            )

        elif (
            item.resolution_status == ResolutionStatus.MISSING
            or item.service_id is None
        ):
            issues.append(
                f"'{item.requested_service}' was not found "
                "in the catalog. Price unavailable — "
                "review required."
            )

        elif item.unit_price is None:
            issues.append(
                f"'{item.requested_service}' is missing "
                "a catalog price."
            )

        elif item.price_source != "service_catalog":
            issues.append(
                f"'{item.requested_service}' does not have "
                "a catalog-verified price."
            )

    return issues


def _candidates_for_item(
    item: InvoiceItem,
    catalog: list[CatalogService],
) -> list[ServiceCandidateOut]:
    if (
        item.resolution_status
        != ResolutionStatus.AMBIGUOUS
    ):
        return []

    result = match_requested_item(
        item.requested_service,
        catalog,
    )

    return [
        _candidate_out(
            option,
            result.score,
        )
        for option in result.options
    ]


def serialize_invoice(
    invoice: Invoice,
    catalog: list[CatalogService] | None = None,
) -> InvoiceOut:
    catalog = catalog or []

    items = []

    for item in invoice.items:
        payload = InvoiceItemOut.model_validate(
            item
        )

        payload.candidate_services = (
            _candidates_for_item(
                item,
                catalog,
            )
        )

        items.append(payload)

    audit = [
        AuditLogOut(
            id=log.id,
            invoice_id=log.invoice_id,
            event_type=log.event_type,
            metadata=log.event_metadata,
            created_at=log.created_at,
        )
        for log in sorted(
            invoice.audit_logs,
            key=lambda row: row.created_at,
        )
    ]

    return InvoiceOut(
        id=invoice.id,
        invoice_number=invoice.invoice_number,
        customer_id=invoice.customer_id,
        status=invoice.status,
        currency=invoice.currency,
        subtotal=invoice.subtotal,
        tax_rate=invoice.tax_rate,
        tax_amount=invoice.tax_amount,
        total=invoice.total,
        notes=invoice.notes,
        source_message=invoice.source_message,
        created_at=invoice.created_at,
        updated_at=invoice.updated_at,
        approved_at=invoice.approved_at,
        exported_at=invoice.exported_at,
        customer=CustomerOut.model_validate(
            invoice.customer
        ),
        items=items,
        audit_logs=audit,
        approval_blockers=approval_blockers(
            invoice
        ),
    )


def create_invoice(
    db: Session,
    payload: InvoiceCreateIn,
    user: User,
) -> Invoice:
    # Only this user's catalog is loaded.
    catalog = load_catalog(
        db,
        user,
    )

    workspace_settings = get_or_create_settings(
        db,
        user,
    )

    customer = upsert_customer(
        db,
        payload.customer,
        user,
    )

    currency = (
        payload.currency.strip().upper()
        if payload.currency
        else workspace_settings.default_currency
    )

    if payload.tax_rate is not None:
        tax_rate = money(payload.tax_rate)

    elif (
        workspace_settings.tax_enabled
        and workspace_settings.tax_type != "NONE"
    ):
        tax_rate = money(
            workspace_settings.default_tax_rate
        )

    else:
        tax_rate = Decimal("0.00")

    invoice = Invoice(
        invoice_number=generate_invoice_number(db),
        customer=customer,
        user_id=user.id,
        status=InvoiceStatus.DRAFT,

        # Financial settings used by this invoice.
        currency=currency,
        tax_rate=tax_rate,

        # Business/payment snapshot.
        company_name_snapshot=(
            workspace_settings.company_name
        ),
        company_email_snapshot=(
            workspace_settings.company_email
        ),
        company_address_snapshot=(
            workspace_settings.company_address
        ),
        payment_information_snapshot=(
            workspace_settings.payment_information
        ),
        tax_enabled_snapshot=(
            workspace_settings.tax_enabled
        ),
        tax_type_snapshot=(
            workspace_settings.tax_type
        ),
        gstin_snapshot=(
            workspace_settings.gstin
        ),
        business_state_snapshot=(
            workspace_settings.business_state
        ),

        notes=payload.notes,
        source_message=payload.source_message,
    )

    db.add(invoice)
    db.flush()

    # ---------------------------------------------------------------
    # Create invoice line items
    # ---------------------------------------------------------------

    for item_in in payload.items:
        try:
            quantity = quantity_value(
                item_in.quantity
            )

        except ValueError as exc:
            raise AppError(
                str(exc),
                status_code=422,
                code="invalid_quantity",
            ) from exc

        requested_service = (
            item_in.requested_service.strip()
        )

        if not requested_service:
            raise AppError(
                "Requested service cannot be empty.",
                status_code=422,
                code="invalid_service",
            )

        item = InvoiceItem(
            invoice_id=invoice.id,
            requested_service=requested_service,
            quantity=quantity,
            notes=item_in.notes,
        )

        chosen = None

        if item_in.service_id:
            chosen = _get_user_service(
                db,
                item_in.service_id,
                user,
            )

        apply_match_to_item(
            item,
            requested_service,
            catalog,
            chosen=chosen,
        )

        invoice.items.append(item)

        # -----------------------------------------------------------
        # Audit service resolution
        # -----------------------------------------------------------

        if item.resolution_status == ResolutionStatus.MATCHED:
            add_audit(
                db,
                invoice.id,
                "service_matched",
                {
                    "item_id": str(item.id),
                    "requested_service": requested_service,
                    "service_name": item.service_name_snapshot,
                    "match_score": (
                        str(item.match_score)
                        if item.match_score is not None
                        else None
                    ),
                    "method": (
                        "manual"
                        if chosen is not None
                        else "catalog_match"
                    ),
                },
            )

            add_audit(
                db,
                invoice.id,
                "price_resolved",
                {
                    "service_name": item.service_name_snapshot,
                    "unit_price": (
                        str(item.unit_price)
                        if item.unit_price is not None
                        else None
                    ),
                    "price_source": item.price_source,
                },
            )

        elif item.resolution_status == ResolutionStatus.AMBIGUOUS:
            add_audit(
                db,
                invoice.id,
                "service_ambiguous",
                {
                    "item_id": str(item.id),
                    "requested_service": requested_service,
                    "match_score": (
                        str(item.match_score)
                        if item.match_score is not None
                        else None
                    ),
                },
            )

        elif item.resolution_status == ResolutionStatus.MISSING:
            add_audit(
                db,
                invoice.id,
                "service_missing",
                {
                    "item_id": str(item.id),
                    "requested_service": requested_service,
                    "match_score": (
                        str(item.match_score)
                        if item.match_score is not None
                        else None
                    ),
                },
            )

    # ---------------------------------------------------------------
    # Calculate deterministic invoice totals
    # ---------------------------------------------------------------

    recalculate_invoice(invoice)

    invoice.status = derive_status(
        invoice
    )

    # ---------------------------------------------------------------
    # Invoice-level audit events
    # ---------------------------------------------------------------

    add_audit(
        db,
        invoice.id,
        "invoice_created",
        {
            "invoice_number": invoice.invoice_number,
            "currency": invoice.currency,
            "tax_rate": str(invoice.tax_rate),
            "status": invoice.status.value,
            "subtotal": str(invoice.subtotal),
            "tax_amount": str(invoice.tax_amount),
            "total": str(invoice.total),
        },
    )

    if payload.source_message:
        add_audit(
            db,
            invoice.id,
            "ai_extraction_completed",
            {
                "source": "groq_structured_output",
            },
        )

    db.commit()

    return get_invoice_or_404(
        db,
        invoice.id,
        user,
    )


def update_invoice(
    db: Session,
    invoice_id: UUID,
    payload: InvoiceUpdateIn,
    user: User,
) -> Invoice:
    invoice = get_invoice_or_404(
        db,
        invoice_id,
        user,
    )

    if invoice.status in LOCKED_STATUSES:
        raise ConflictError(
            "Approved invoices cannot be edited."
        )

    # Only this user's catalog is loaded.
    catalog = load_catalog(
        db,
        user,
    )

    if payload.customer:
        invoice.customer_id = (
            upsert_customer(
                db,
                payload.customer,
                user,
            ).id
        )

        db.flush()

        invoice.customer = db.get(
            Customer,
            invoice.customer_id,
        )

    if payload.tax_rate is not None:
        invoice.tax_rate = money(
            payload.tax_rate
        )

    if payload.notes is not None:
        invoice.notes = payload.notes

    if payload.items is not None:
        invoice.items.clear()

        db.flush()

        for item_in in payload.items:
            try:
                qty = quantity_value(
                    item_in.quantity
                )

            except ValueError as exc:
                raise AppError(
                    str(exc),
                    status_code=422,
                    code="invalid_quantity",
                ) from exc

            requested_service = (
                item_in.requested_service.strip()
            )

            if not requested_service:
                raise AppError(
                    "Requested service cannot be empty.",
                    status_code=422,
                    code="invalid_service",
                )

            item = InvoiceItem(
                invoice_id=invoice.id,
                requested_service=requested_service,
                quantity=qty,
                notes=item_in.notes,
            )

            chosen = (
                _get_user_service(
                    db,
                    item_in.service_id,
                    user,
                )
                if item_in.service_id
                else None
            )

            apply_match_to_item(
                item,
                requested_service,
                catalog,
                chosen=chosen,
            )

            invoice.items.append(item)

    recalculate_invoice(invoice)

    invoice.status = derive_status(
        invoice
    )

    add_audit(
        db,
        invoice.id,
        "invoice_edited",
        {
            "status": invoice.status.value,
        },
    )

    db.commit()

    return get_invoice_or_404(
        db,
        invoice.id,
        user,
    )


def resolve_item_service(
    db: Session,
    invoice_id: UUID,
    item_id: UUID,
    service_id: UUID,
    user: User,
) -> Invoice:
    invoice = get_invoice_or_404(
        db,
        invoice_id,
        user,
    )

    if invoice.status in LOCKED_STATUSES:
        raise ConflictError(
            "Approved invoices cannot be edited."
        )

    item = next(
        (
            row
            for row in invoice.items
            if row.id == item_id
        ),
        None,
    )

    if item is None:
        raise NotFoundError(
            "Invoice item not found"
        )

    service = _get_user_service(
        db,
        service_id,
        user,
    )

    apply_match_to_item(
        item,
        item.requested_service,
        load_catalog(
            db,
            user,
        ),
        chosen=service,
    )

    recalculate_invoice(invoice)

    invoice.status = derive_status(
        invoice
    )

    add_audit(
        db,
        invoice.id,
        "service_matched",
        {
            "item_id": str(item.id),
            "requested_service": item.requested_service,
            "service_name": service.name,
            "method": "manual",
        },
    )

    add_audit(
        db,
        invoice.id,
        "price_resolved",
        {
            "service_name": service.name,
            "unit_price": (
                str(item.unit_price)
                if item.unit_price is not None
                else None
            ),
            "price_source": "service_catalog",
        },
    )

    db.commit()

    return get_invoice_or_404(
        db,
        invoice.id,
        user,
    )


def calculate_existing(
    db: Session,
    invoice_id: UUID,
    user: User,
) -> Invoice:
    invoice = get_invoice_or_404(
        db,
        invoice_id,
        user,
    )

    if invoice.status in LOCKED_STATUSES:
        return invoice

    recalculate_invoice(invoice)

    invoice.status = derive_status(
        invoice
    )

    db.commit()

    return get_invoice_or_404(
        db,
        invoice.id,
        user,
    )


def approve_invoice(
    db: Session,
    invoice_id: UUID,
    user: User,
) -> Invoice:
    invoice = get_invoice_or_404(
        db,
        invoice_id,
        user,
    )

    if invoice.status in LOCKED_STATUSES:
        return invoice

    recalculate_invoice(invoice)

    issues = approval_blockers(
        invoice
    )

    if issues:
        invoice.status = (
            InvoiceStatus.REVIEW_REQUIRED
        )

        db.commit()

        raise ApprovalBlockedError(
            "Invoice cannot be approved until "
            "all issues are resolved.",
            issues,
        )

    invoice.status = InvoiceStatus.APPROVED
    invoice.approved_at = _now()

    add_audit(
        db,
        invoice.id,
        "invoice_approved",
        {
            "total": str(invoice.total),
        },
    )

    db.commit()

    return get_invoice_or_404(
        db,
        invoice.id,
        user,
    )


def mark_exported(
    db: Session,
    invoice_id: UUID,
    user: User,
) -> Invoice:
    invoice = get_invoice_or_404(
        db,
        invoice_id,
        user,
    )

    if invoice.status not in {
        InvoiceStatus.APPROVED,
        InvoiceStatus.EXPORTED,
    }:
        raise ConflictError(
            "PDF export is only available "
            "after approval."
        )

    invoice.status = InvoiceStatus.EXPORTED
    invoice.exported_at = _now()

    add_audit(
        db,
        invoice.id,
        "invoice_exported",
        {
            "invoice_number": invoice.invoice_number,
        },
    )

    db.commit()

    return get_invoice_or_404(
        db,
        invoice.id,
        user,
    )


def list_invoices(
    db: Session,
    user: User,
    status: InvoiceStatus | None = None,
    customer: str | None = None,
    date_from: datetime | None = None,
    date_to: datetime | None = None,
) -> list[Invoice]:
    stmt = (
        select(Invoice)
        .options(
            selectinload(Invoice.customer)
        )
        .where(
            Invoice.user_id == user.id
        )
        .order_by(
            Invoice.created_at.desc()
        )
    )

    if status:
        stmt = stmt.where(
            Invoice.status == status
        )

    if customer:
        pattern = f"%{customer}%"

        stmt = stmt.join(Customer).where(
            or_(
                Customer.name.ilike(pattern),
                Customer.email.ilike(pattern),
                Customer.company.ilike(pattern),
            )
        )

    if date_from:
        stmt = stmt.where(
            Invoice.created_at >= date_from
        )

    if date_to:
        stmt = stmt.where(
            Invoice.created_at <= date_to
        )

    return list(
        db.execute(stmt)
        .scalars()
        .unique()
        .all()
    )


def to_list_item(
    invoice: Invoice,
) -> InvoiceListOut:
    return InvoiceListOut(
        id=invoice.id,
        invoice_number=invoice.invoice_number,
        customer_name=(
            invoice.customer.name
            if invoice.customer
            else "Unknown"
        ),
        status=invoice.status,
        currency=invoice.currency,
        total=invoice.total,
        created_at=invoice.created_at,
    )