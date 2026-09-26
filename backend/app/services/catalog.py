import csv
import io
import re
from decimal import Decimal, InvalidOperation
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.core.exceptions import NotFoundError
from app.core.money import money
from app.models.entities import (
    Invoice,
    InvoiceStatus,
    Service,
    ServiceAlias,
    User,
)
from app.schemas.common import (
    DashboardOut,
    ServiceImportPreviewOut,
    ServiceImportRowOut,
    ServiceImportOut,
    ServiceIn,
    ServiceOut,
    ServiceUpdate,
)
from app.services.invoices import list_invoices, to_list_item


MAX_IMPORT_BYTES = 2 * 1024 * 1024

REQUIRED_IMPORT_COLUMNS = {"name", "price"}

OPTIONAL_IMPORT_COLUMNS = {
    "description",
    "unit",
    "currency",
    "aliases",
    "code",
    "active",
}


def serialize_service(service: Service) -> ServiceOut:
    return ServiceOut(
        id=service.id,
        code=service.code,
        name=service.name,
        description=service.description,
        unit=service.unit,
        price=money(service.price),
        currency=service.currency,
        active=service.active,
        aliases=[alias.alias for alias in service.aliases],
        created_at=service.created_at,
        updated_at=service.updated_at,
    )


def list_services(
    db: Session,
    user: User,
    query: str | None = None,
    include_inactive: bool = True,
) -> list[Service]:
    stmt = (
        select(Service)
        .options(selectinload(Service.aliases))
        .where(Service.user_id == user.id)
        .order_by(Service.name)
    )

    if not include_inactive:
        stmt = stmt.where(Service.active.is_(True))

    if query:
        pattern = f"%{query}%"

        stmt = stmt.where(
            Service.name.ilike(pattern)
            | Service.code.ilike(pattern)
        )

    return list(
        db.execute(stmt)
        .scalars()
        .unique()
        .all()
    )


def _next_code(
    db: Session,
    user: User,
    name: str,
) -> str:
    slug = "".join(
        ch for ch in name.upper() if ch.isalnum()
    )[:8] or "SVC"

    count = db.execute(
        select(func.count())
        .select_from(Service)
        .where(Service.user_id == user.id)
    ).scalar_one()

    return f"{slug}{int(count) + 1:03d}"


def create_service(
    db: Session,
    user: User,
    payload: ServiceIn,
) -> Service:
    service = Service(
        user_id=user.id,
        code=payload.code or _next_code(
            db,
            user,
            payload.name,
        ),
        name=payload.name,
        description=payload.description,
        unit=payload.unit,
        price=money(payload.price),
        currency=payload.currency,
        active=payload.active,
    )

    db.add(service)
    db.flush()

    for alias in payload.aliases:
        cleaned = alias.strip()

        if cleaned:
            db.add(
                ServiceAlias(
                    service_id=service.id,
                    alias=cleaned,
                )
            )

    db.commit()
    db.refresh(service)

    return db.execute(
        select(Service)
        .options(selectinload(Service.aliases))
        .where(Service.id == service.id)
    ).scalar_one()


def update_service(
    db: Session,
    user: User,
    service_id: UUID,
    payload: ServiceUpdate,
) -> Service:
    service = db.execute(
        select(Service)
        .options(selectinload(Service.aliases))
        .where(
            Service.id == service_id,
            Service.user_id == user.id,
        )
    ).scalar_one_or_none()

    if service is None:
        raise NotFoundError("Service not found")

    if payload.name is not None:
        service.name = payload.name

    if payload.description is not None:
        service.description = payload.description

    if payload.unit is not None:
        service.unit = payload.unit

    if payload.price is not None:
        service.price = money(payload.price)

    if payload.currency is not None:
        service.currency = payload.currency

    if payload.active is not None:
        service.active = payload.active

    if payload.aliases is not None:
        service.aliases.clear()
        db.flush()

        for alias in payload.aliases:
            cleaned = alias.strip()

            if cleaned:
                service.aliases.append(
                    ServiceAlias(alias=cleaned)
                )

    db.commit()

    return db.execute(
        select(Service)
        .options(selectinload(Service.aliases))
        .where(Service.id == service.id)
    ).scalar_one()


def deactivate_service(
    db: Session,
    user: User,
    service_id: UUID,
) -> Service:
    return update_service(
        db,
        user,
        service_id,
        ServiceUpdate(active=False),
    )


def _clean_csv_value(value: str | None) -> str:
    if value is None:
        return ""

    return value.strip()


def _parse_aliases(value: str) -> list[str]:
    if not value:
        return []

    parts = re.split(r"[|;]", value)

    return [
        item.strip()
        for item in parts
        if item.strip()
    ]


def _parse_bool(value: str) -> bool:
    if not value:
        return True

    normalized = value.strip().lower()

    if normalized in {"true", "1", "yes", "y", "active"}:
        return True

    if normalized in {
        "false",
        "0",
        "no",
        "n",
        "inactive",
    }:
        return False

    raise ValueError(
        "active must be true/false, yes/no, 1/0, or active/inactive"
    )


def _parse_decimal(value: str) -> Decimal:
    try:
        parsed = Decimal(value)

    except (InvalidOperation, ValueError):
        raise ValueError("price must be a valid number")

    if parsed < 0:
        raise ValueError("price cannot be negative")

    return money(parsed)


def _normalize_headers(
    fieldnames: list[str | None] | None,
) -> list[str]:
    if not fieldnames:
        return []

    return [
        _clean_csv_value(field).lower()
        for field in fieldnames
        if field is not None
    ]


def _validate_csv_rows(
    db: Session,
    user: User,
    content: bytes,
) -> ServiceImportPreviewOut:
    if len(content) > MAX_IMPORT_BYTES:
        raise ValueError(
            "CSV file is too large. Maximum size is 2 MB."
        )

    try:
        text = content.decode("utf-8-sig")

    except UnicodeDecodeError:
        raise ValueError(
            "CSV must be UTF-8 encoded."
        )

    try:
        reader = csv.DictReader(
            io.StringIO(text)
        )

        headers = _normalize_headers(
            reader.fieldnames
        )

        if not headers:
            raise ValueError(
                "CSV does not contain a header row."
            )

        missing = (
            REQUIRED_IMPORT_COLUMNS - set(headers)
        )

        if missing:
            raise ValueError(
                "CSV is missing required columns: "
                + ", ".join(sorted(missing))
            )

        unsupported = (
            set(headers)
            - REQUIRED_IMPORT_COLUMNS
            - OPTIONAL_IMPORT_COLUMNS
        )

        if unsupported:
            raise ValueError(
                "Unsupported CSV columns: "
                + ", ".join(sorted(unsupported))
            )

        # Only check services belonging to the
        # currently authenticated user's catalog.
        existing_services = db.execute(
            select(Service.name, Service.code)
            .where(Service.user_id == user.id)
        ).all()

        existing_names = {
            name.strip().casefold()
            for name, _ in existing_services
        }

        existing_codes = {
            code.strip().casefold()
            for _, code in existing_services
        }

        seen_names: set[str] = set()
        seen_codes: set[str] = set()

        rows: list[ServiceImportRowOut] = []

        valid_rows = 0
        invalid_rows = 0
        duplicate_rows = 0

        for row_number, raw_row in enumerate(
            reader,
            start=2,
        ):
            row = {
                str(key).strip().lower(): (
                    value if value is not None else ""
                )
                for key, value in raw_row.items()
                if key is not None
            }

            name = _clean_csv_value(
                row.get("name")
            )

            description = _clean_csv_value(
                row.get("description")
            ) or None

            unit = (
                _clean_csv_value(
                    row.get("unit")
                )
                or "project"
            )

            price_value = _clean_csv_value(
                row.get("price")
            )

            currency = (
                _clean_csv_value(
                    row.get("currency")
                )
                or "INR"
            ).upper()

            code = _clean_csv_value(
                row.get("code")
            ) or None

            aliases = _parse_aliases(
                _clean_csv_value(
                    row.get("aliases")
                )
            )

            status = "ready"
            message: str | None = None

            if not name:
                status = "invalid"
                message = "Service name is required."

            elif not price_value:
                status = "invalid"
                message = "Price is required."

            else:
                try:
                    _parse_decimal(price_value)
                except ValueError as exc:
                    status = "invalid"
                    message = str(exc)

            if status == "ready":
                name_key = name.casefold()

                if name_key in existing_names:
                    status = "duplicate"
                    message = (
                        "A service with this name "
                        "already exists."
                    )

                elif name_key in seen_names:
                    status = "duplicate"
                    message = (
                        "This service name appears "
                        "more than once in the CSV."
                    )

                else:
                    seen_names.add(name_key)

            if (
                status == "ready"
                and code is not None
            ):
                code_key = code.casefold()

                if code_key in existing_codes:
                    status = "duplicate"
                    message = (
                        "A service with this code "
                        "already exists."
                    )

                elif code_key in seen_codes:
                    status = "duplicate"
                    message = (
                        "This service code appears "
                        "more than once in the CSV."
                    )

                else:
                    seen_codes.add(code_key)

            if status == "ready":
                valid_rows += 1

            elif status == "duplicate":
                duplicate_rows += 1

            else:
                invalid_rows += 1

            rows.append(
                ServiceImportRowOut(
                    row_number=row_number,
                    name=name or None,
                    description=description,
                    unit=unit,
                    price=price_value or None,
                    currency=currency,
                    aliases=aliases,
                    code=code,
                    status=status,
                    message=message,
                )
            )

        if not rows:
            raise ValueError(
                "CSV does not contain any service rows."
            )

        return ServiceImportPreviewOut(
            total_rows=len(rows),
            valid_rows=valid_rows,
            invalid_rows=invalid_rows,
            duplicate_rows=duplicate_rows,
            rows=rows,
        )

    except csv.Error as exc:
        raise ValueError(
            f"Could not read CSV: {exc}"
        )


def preview_catalog_import(
    db: Session,
    user: User,
    content: bytes,
) -> ServiceImportPreviewOut:
    return _validate_csv_rows(
        db,
        user,
        content,
    )


def import_catalog(
    db: Session,
    user: User,
    content: bytes,
) -> ServiceImportOut:
    preview = _validate_csv_rows(
        db,
        user,
        content,
    )

    if (
        preview.invalid_rows > 0
        or preview.duplicate_rows > 0
    ):
        raise ValueError(
            "Import stopped because the CSV contains "
            "invalid or duplicate rows. Review the "
            "preview and correct the file first."
        )

    imported: list[Service] = []

    try:
        for row in preview.rows:
            service = Service(
                user_id=user.id,
                code=row.code
                or _next_code(
                    db,
                    user,
                    row.name or "Service",
                ),
                name=row.name or "",
                description=row.description,
                unit=row.unit or "project",
                price=_parse_decimal(
                    row.price or "0"
                ),
                currency=row.currency or "INR",
                active=True,
            )

            db.add(service)
            db.flush()

            for alias in row.aliases:
                db.add(
                    ServiceAlias(
                        service_id=service.id,
                        alias=alias,
                    )
                )

            imported.append(service)

        db.commit()

    except Exception:
        db.rollback()
        raise

    services = [
        db.execute(
            select(Service)
            .options(selectinload(Service.aliases))
            .where(Service.id == service.id)
        ).scalar_one()
        for service in imported
    ]

    return ServiceImportOut(
        imported_count=len(services),
        services=[
            serialize_service(service)
            for service in services
        ],
    )


def dashboard_stats(
    db: Session,
    user: User,
) -> DashboardOut:
    invoices = list_invoices(
        db,
        user=user,
    )

    total_revenue = money(
        sum(
            (
                row.total
                for row in invoices
                if row.status
                in {
                    InvoiceStatus.APPROVED,
                    InvoiceStatus.EXPORTED,
                }
            ),
            Decimal("0"),
        )
    )

    return DashboardOut(
        total_invoices=len(invoices),
        drafts=sum(
            1
            for row in invoices
            if row.status == InvoiceStatus.DRAFT
        ),
        pending_review=sum(
            1
            for row in invoices
            if row.status == InvoiceStatus.REVIEW_REQUIRED
        ),
        approved=sum(
            1
            for row in invoices
            if row.status == InvoiceStatus.APPROVED
        ),
        exported=sum(
            1
            for row in invoices
            if row.status == InvoiceStatus.EXPORTED
        ),
        total_revenue=total_revenue,
        recent=[
            to_list_item(row)
            for row in invoices[:8]
        ],
    )