from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, field_validator


ALLOWED_TAX_TYPES = {
    "GST",
    "CUSTOM",
    "NONE",
}

ALLOWED_CURRENCIES = {
    "INR",
    "USD",
    "EUR",
    "GBP",
}


class SettingsOut(BaseModel):
    id: UUID
    user_id: UUID

    company_name: str
    company_email: EmailStr
    company_address: str
    payment_information: str

    default_currency: str

    tax_enabled: bool
    tax_type: str
    default_tax_rate: Decimal

    gstin: str | None
    business_state: str | None


class SettingsUpdateIn(BaseModel):
    company_name: str = Field(
        min_length=1,
        max_length=200,
    )

    company_email: EmailStr

    company_address: str = Field(
        min_length=1,
        max_length=5000,
    )

    payment_information: str = Field(
        min_length=1,
        max_length=5000,
    )

    default_currency: str = Field(
        min_length=3,
        max_length=8,
    )

    tax_enabled: bool

    tax_type: str

    default_tax_rate: Decimal = Field(
        ge=0,
        le=100,
    )

    gstin: str | None = Field(
        default=None,
        max_length=30,
    )

    business_state: str | None = Field(
        default=None,
        max_length=100,
    )

    @field_validator("tax_type")
    @classmethod
    def validate_tax_type(cls, value: str) -> str:
        value = value.strip().upper()

        if value not in ALLOWED_TAX_TYPES:
            raise ValueError(
                "Tax type must be GST, CUSTOM, or NONE."
            )

        return value

    @field_validator("default_currency")
    @classmethod
    def validate_currency(cls, value: str) -> str:
        value = value.strip().upper()

        if value not in ALLOWED_CURRENCIES:
            raise ValueError(
                "Unsupported currency."
            )

        return value

    @field_validator("default_tax_rate")
    @classmethod
    def validate_tax_rate(
        cls,
        value: Decimal,
    ) -> Decimal:
        return value.quantize(Decimal("0.0001"))