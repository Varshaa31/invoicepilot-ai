from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user
from app.db.session import get_db
from app.models.entities import User
from app.schemas.settings import (
    SettingsOut,
    SettingsUpdateIn,
)
from app.services.settings import (
    get_or_create_settings,
    update_settings,
)


router = APIRouter(
    prefix="/settings",
    tags=["settings"],
)


def serialize_settings(
    settings,
) -> SettingsOut:
    return SettingsOut(
        id=settings.id,
        user_id=settings.user_id,
        company_name=settings.company_name,
        company_email=settings.company_email,
        company_address=settings.company_address,
        payment_information=(
            settings.payment_information
        ),
        default_currency=settings.default_currency,
        tax_enabled=settings.tax_enabled,
        tax_type=settings.tax_type,
        default_tax_rate=settings.default_tax_rate,
        gstin=settings.gstin,
        business_state=settings.business_state,
    )


@router.get(
    "",
    response_model=SettingsOut,
)
def get_settings(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> SettingsOut:
    settings = get_or_create_settings(
        db,
        user,
    )

    return serialize_settings(settings)


@router.put(
    "",
    response_model=SettingsOut,
)
def save_settings(
    payload: SettingsUpdateIn,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> SettingsOut:
    settings = update_settings(
        db,
        user,
        payload,
    )

    return serialize_settings(settings)