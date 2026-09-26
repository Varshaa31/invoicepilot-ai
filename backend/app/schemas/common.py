from datetime import datetime
from decimal import Decimal
from typing import Annotated
from uuid import UUID

from pydantic import (
    BaseModel,
    ConfigDict,
    EmailStr,
    Field,
    PlainSerializer,
    field_validator,
)

from app.core.money import money
from app.models.entities import InvoiceStatus, ResolutionStatus


Money = Annotated[
    Decimal,
    PlainSerializer(
        lambda value: f"{money(value):.2f}",
        return_type=str,
    ),
]


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class CustomerExtract(BaseModel):
    name: str | None = None
    email: str | None = None
    phone: str | None = None
    company: str | None = None

    @field_validator("email", "name", "phone", "company", mode="before")
    @classmethod
    def blank_to_none(cls, value):
        if value is None:
            return None

        if isinstance(value, str) and not value.strip():
            return None

        return value


class InvoiceItemRequest(BaseModel):
    requested_service: str = Field(min_length=1)
    quantity: Decimal | None = Field(default=None, gt=0)
    notes: str | None = None


class InvoiceRequest(BaseModel):
    customer: CustomerExtract
    requested_items: list[InvoiceItemRequest] = Field(min_length=1)
    notes: str | None = None
    missing_information: list[str] = Field(default_factory=list)


class ExtractionIn(BaseModel):
    customer_message: str = Field(min_length=1)


class ServiceCandidateOut(ORMModel):
    service_id: UUID
    name: str
    description: str | None = None
    unit_price: Money
    currency: str
    match_score: float | None = None


class ItemMatchOut(BaseModel):
    requested_service: str
    quantity: Decimal | None = None
    notes: str | None = None
    status: ResolutionStatus
    matched_service: ServiceCandidateOut | None = None
    candidate_services: list[ServiceCandidateOut] = Field(default_factory=list)
    unit_price: Money | None = None
    currency: str | None = None
    price_source: str | None = None
    match_score: float | None = None


class ExtractionOut(BaseModel):
    extraction: InvoiceRequest
    matches: list[ItemMatchOut]


class CustomerIn(BaseModel):
    name: str = Field(min_length=1)
    email: EmailStr | None = None
    phone: str | None = None
    company: str | None = None
    address: str | None = None

    @field_validator("email", mode="before")
    @classmethod
    def empty_email(cls, value):
        if value is None or (
            isinstance(value, str) and not value.strip()
        ):
            return None

        return value


class CustomerOut(ORMModel):
    id: UUID
    name: str
    email: str | None
    phone: str | None
    company: str | None
    address: str | None
    created_at: datetime
    updated_at: datetime


class ServiceIn(BaseModel):
    name: str = Field(min_length=1)
    description: str | None = None
    unit: str = "project"
    price: Decimal = Field(ge=0)
    currency: str = "INR"
    active: bool = True
    aliases: list[str] = Field(default_factory=list)
    code: str | None = None


class ServiceUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    unit: str | None = None
    price: Decimal | None = Field(default=None, ge=0)
    currency: str | None = None
    active: bool | None = None
    aliases: list[str] | None = None


class ServiceOut(ORMModel):
    id: UUID
    code: str
    name: str
    description: str | None
    unit: str
    price: Money
    currency: str
    active: bool
    aliases: list[str] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime


class ServiceImportRowOut(BaseModel):
    row_number: int
    name: str | None = None
    description: str | None = None
    unit: str | None = None
    price: str | None = None
    currency: str | None = None
    aliases: list[str] = Field(default_factory=list)
    code: str | None = None
    status: str
    message: str | None = None


class ServiceImportPreviewOut(BaseModel):
    total_rows: int
    valid_rows: int
    invalid_rows: int
    duplicate_rows: int
    rows: list[ServiceImportRowOut]


class ServiceImportOut(BaseModel):
    imported_count: int
    services: list[ServiceOut]


class InvoiceItemIn(BaseModel):
    requested_service: str = Field(min_length=1)
    quantity: Decimal = Field(gt=0)
    notes: str | None = None
    service_id: UUID | None = None


class InvoiceCreateIn(BaseModel):
    customer: CustomerIn
    items: list[InvoiceItemIn] = Field(min_length=1)
    notes: str | None = None
    tax_rate: Decimal | None = Field(default=None, ge=0, le=100)
    currency: str | None = None
    source_message: str | None = None


class InvoiceUpdateIn(BaseModel):
    customer: CustomerIn | None = None
    items: list[InvoiceItemIn] | None = None
    notes: str | None = None
    tax_rate: Decimal | None = Field(default=None, ge=0, le=100)


class ResolveServiceIn(BaseModel):
    item_id: UUID
    service_id: UUID


class InvoiceItemOut(ORMModel):
    id: UUID
    invoice_id: UUID
    service_id: UUID | None
    requested_service: str
    service_name_snapshot: str | None
    quantity: Money
    unit_price: Money | None
    line_total: Money | None
    resolution_status: ResolutionStatus
    match_score: Decimal | None
    price_source: str
    notes: str | None
    candidate_services: list[ServiceCandidateOut] = Field(
        default_factory=list
    )


class AuditLogOut(ORMModel):
    id: UUID
    invoice_id: UUID
    event_type: str
    metadata: dict | None = None
    created_at: datetime


class InvoiceOut(ORMModel):
    id: UUID
    invoice_number: str
    customer_id: UUID
    status: InvoiceStatus
    currency: str
    subtotal: Money
    tax_rate: Money
    tax_amount: Money
    total: Money
    notes: str | None
    source_message: str | None
    created_at: datetime
    updated_at: datetime
    approved_at: datetime | None
    exported_at: datetime | None
    customer: CustomerOut
    items: list[InvoiceItemOut]
    audit_logs: list[AuditLogOut] = Field(default_factory=list)
    approval_blockers: list[str] = Field(default_factory=list)


class InvoiceListOut(ORMModel):
    id: UUID
    invoice_number: str
    customer_name: str
    status: InvoiceStatus
    currency: str
    total: Money
    created_at: datetime


class DashboardOut(BaseModel):
    total_invoices: int
    drafts: int
    pending_review: int
    approved: int
    exported: int
    total_revenue: Money
    recent: list[InvoiceListOut]


class HealthOut(BaseModel):
    status: str
    database: str
    groq_configured: bool