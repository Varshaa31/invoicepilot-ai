from datetime import date
from decimal import Decimal
from pydantic import BaseModel, ConfigDict, Field, EmailStr


class Customer(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str | None = None
    email: EmailStr | None = None


class InvoiceItem(BaseModel):
    model_config = ConfigDict(extra="forbid")
    requested_service: str = Field(min_length=1)
    quantity: int | None = Field(default=None, ge=1)
    notes: str | None = None


class InvoiceRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    customer: Customer
    items: list[InvoiceItem] = Field(min_length=1)
    notes: str | None = None
    missing_information: list[str] = Field(default_factory=list)
    ambiguous_items: list[str] = Field(default_factory=list)


class InvoiceLine(BaseModel):
    model_config = ConfigDict(extra="forbid")
    service_id: str
    description: str
    quantity: int = Field(ge=1)
    unit_price: Decimal = Field(ge=0)
    notes: str | None = None
    line_total: Decimal = Decimal("0")


class InvoiceDraft(BaseModel):
    model_config = ConfigDict(extra="forbid")
    invoice_number: str
    issue_date: date
    due_date: date
    seller_name: str
    seller_email: EmailStr | None = None
    customer: Customer
    lines: list[InvoiceLine]
    tax_rate: Decimal = Field(ge=0, le=100)
    discount: Decimal = Field(default=Decimal("0"), ge=0)
    currency: str = "INR"
    notes: str | None = None
    subtotal: Decimal = Decimal("0")
    tax: Decimal = Decimal("0")
    grand_total: Decimal = Decimal("0")
