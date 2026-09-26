from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.entities import User, WorkspaceSettings
from app.schemas.settings import SettingsUpdateIn


def get_or_create_settings(
    db: Session,
    user: User,
) -> WorkspaceSettings:
    settings = db.scalar(
        select(WorkspaceSettings).where(
            WorkspaceSettings.user_id == user.id
        )
    )

    if settings:
        return settings

    settings = WorkspaceSettings(
        user_id=user.id,
        company_name=user.workspace_name
        or "InvoicePilot AI",
        company_email=user.email,
        company_address="Bengaluru, India",
        payment_information=(
            "Bank transfer · A/C InvoicePilot AI · "
            "IFSC DEMO0001234"
        ),
        default_currency="INR",
        tax_enabled=True,
        tax_type="GST",
        default_tax_rate=Decimal("18.00"),
    )

    db.add(settings)
    db.commit()
    db.refresh(settings)

    return settings


def update_settings(
    db: Session,
    user: User,
    payload: SettingsUpdateIn,
) -> WorkspaceSettings:
    settings = get_or_create_settings(
        db,
        user,
    )

    settings.company_name = (
        payload.company_name.strip()
    )

    settings.company_email = (
        str(payload.company_email).strip().lower()
    )

    settings.company_address = (
        payload.company_address.strip()
    )

    settings.payment_information = (
        payload.payment_information.strip()
    )

    settings.default_currency = (
        payload.default_currency.upper()
    )

    settings.tax_enabled = payload.tax_enabled

    settings.tax_type = (
        payload.tax_type.upper()
    )

    if not payload.tax_enabled:
        settings.default_tax_rate = Decimal("0.00")
    elif settings.tax_type == "NONE":
        settings.default_tax_rate = Decimal("0.00")
    else:
        settings.default_tax_rate = (
            payload.default_tax_rate
        )

    settings.gstin = (
        payload.gstin.strip()
        if payload.gstin
        else None
    )

    settings.business_state = (
        payload.business_state.strip()
        if payload.business_state
        else None
    )

    db.commit()
    db.refresh(settings)

    return settings