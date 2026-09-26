import enum
import uuid
from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    ForeignKey,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import JSON, Uuid

from app.db.base import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class InvoiceStatus(str, enum.Enum):
    DRAFT = "DRAFT"
    REVIEW_REQUIRED = "REVIEW_REQUIRED"
    READY_FOR_APPROVAL = "READY_FOR_APPROVAL"
    APPROVED = "APPROVED"
    EXPORTED = "EXPORTED"


class ResolutionStatus(str, enum.Enum):
    MATCHED = "MATCHED"
    AMBIGUOUS = "AMBIGUOUS"
    MISSING = "MISSING"


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        primary_key=True,
        default=uuid.uuid4,
    )
    name: Mapped[str] = mapped_column(
        String(120),
        nullable=False,
    )
    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
    )
    workspace_name: Mapped[str] = mapped_column(
        String(120),
        nullable=False,
        default="Demo Workspace",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utcnow,
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )
    password_hash: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )
    email_verified: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )


class WorkspaceSettings(Base):
    __tablename__ = "workspace_settings"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        primary_key=True,
        default=uuid.uuid4,
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )

    company_name: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        default="InvoicePilot AI",
    )

    company_email: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        default="billing@invoicepilot.demo",
    )

    company_address: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        default="Bengaluru, India",
    )

    payment_information: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        default="Bank transfer · A/C InvoicePilot AI · IFSC DEMO0001234",
    )

    default_currency: Mapped[str] = mapped_column(
        String(8),
        nullable=False,
        default="INR",
    )

    tax_enabled: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
    )

    tax_type: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="GST",
    )

    default_tax_rate: Mapped[Decimal] = mapped_column(
        Numeric(7, 4),
        nullable=False,
        default=Decimal("18.00"),
    )

    gstin: Mapped[str | None] = mapped_column(
        String(30),
        nullable=True,
    )

    business_state: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utcnow,
        server_default=func.now(),
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    user: Mapped[User] = relationship()


class Customer(Base):
    __tablename__ = "customers"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        primary_key=True,
        default=uuid.uuid4,
    )
    name: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
    )
    email: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )
    phone: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )
    company: Mapped[str | None] = mapped_column(
        String(200),
        nullable=True,
    )
    address: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utcnow,
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    invoices: Mapped[list["Invoice"]] = relationship(
        back_populates="customer"
    )


class Service(Base):
    __tablename__ = "services"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        primary_key=True,
        default=uuid.uuid4,
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )

    code: Mapped[str] = mapped_column(
        String(40),
        nullable=False,
    )

    name: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    unit: Mapped[str] = mapped_column(
        String(40),
        nullable=False,
        default="project",
    )

    price: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
    )

    currency: Mapped[str] = mapped_column(
        String(8),
        nullable=False,
        default="INR",
    )

    active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    user: Mapped["User"] = relationship()

    aliases: Mapped[list["ServiceAlias"]] = relationship(
        back_populates="service",
        cascade="all, delete-orphan",
    )


class ServiceAlias(Base):
    __tablename__ = "service_aliases"

    __table_args__ = (
        UniqueConstraint(
            "service_id",
            "alias",
            name="uq_service_alias",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        primary_key=True,
        default=uuid.uuid4,
    )
    service_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("services.id"),
        nullable=False,
    )
    alias: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
    )

    service: Mapped[Service] = relationship(
        back_populates="aliases"
    )


class Invoice(Base):
    __tablename__ = "invoices"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        primary_key=True,
        default=uuid.uuid4,
    )

    invoice_number: Mapped[str] = mapped_column(
        String(40),
        unique=True,
        nullable=False,
    )

    customer_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("customers.id"),
        nullable=False,
    )

    status: Mapped[InvoiceStatus] = mapped_column(
        Enum(
            InvoiceStatus,
            name="invoice_status",
            native_enum=False,
        ),
        nullable=False,
        default=InvoiceStatus.DRAFT,
    )

    user: Mapped[User | None] = relationship()

    user_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    # ---------------------------------------------------------------
    # Financial values
    # ---------------------------------------------------------------

    currency: Mapped[str] = mapped_column(
        String(8),
        nullable=False,
        default="INR",
    )

    subtotal: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
        default=Decimal("0.00"),
    )

    tax_rate: Mapped[Decimal] = mapped_column(
        Numeric(7, 4),
        nullable=False,
        default=Decimal("18.00"),
    )

    tax_amount: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
        default=Decimal("0.00"),
    )

    total: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
        default=Decimal("0.00"),
    )

    # ---------------------------------------------------------------
    # Invoice settings snapshot
    #
    # These values are copied from WorkspaceSettings when the
    # invoice is created. They are intentionally stored on the
    # invoice so later Settings changes do not rewrite old invoices.
    # ---------------------------------------------------------------

    company_name_snapshot: Mapped[str | None] = mapped_column(
        String(200),
        nullable=True,
    )

    company_email_snapshot: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    company_address_snapshot: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    payment_information_snapshot: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    tax_enabled_snapshot: Mapped[bool | None] = mapped_column(
        Boolean,
        nullable=True,
    )

    tax_type_snapshot: Mapped[str | None] = mapped_column(
        String(30),
        nullable=True,
    )

    gstin_snapshot: Mapped[str | None] = mapped_column(
        String(30),
        nullable=True,
    )

    business_state_snapshot: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    # ---------------------------------------------------------------
    # Other invoice data
    # ---------------------------------------------------------------

    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    source_message: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utcnow,
        server_default=func.now(),
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    approved_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    exported_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    customer: Mapped[Customer] = relationship(
        back_populates="invoices"
    )

    items: Mapped[list["InvoiceItem"]] = relationship(
        back_populates="invoice",
        cascade="all, delete-orphan",
        order_by="InvoiceItem.created_at",
    )

    audit_logs: Mapped[list["AuditLog"]] = relationship(
        back_populates="invoice",
        cascade="all, delete-orphan",
        order_by="AuditLog.created_at",
    )


class InvoiceItem(Base):
    __tablename__ = "invoice_items"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        primary_key=True,
        default=uuid.uuid4,
    )

    invoice_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("invoices.id"),
        nullable=False,
    )

    service_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("services.id"),
        nullable=True,
    )

    requested_service: Mapped[str] = mapped_column(
        String(300),
        nullable=False,
    )

    service_name_snapshot: Mapped[str | None] = mapped_column(
        String(200),
        nullable=True,
    )

    quantity: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
        default=Decimal("1.00"),
    )

    unit_price: Mapped[Decimal | None] = mapped_column(
        Numeric(12, 2),
        nullable=True,
    )

    line_total: Mapped[Decimal | None] = mapped_column(
        Numeric(12, 2),
        nullable=True,
    )

    resolution_status: Mapped[ResolutionStatus] = mapped_column(
        Enum(
            ResolutionStatus,
            name="resolution_status",
            native_enum=False,
        ),
        nullable=False,
        default=ResolutionStatus.MISSING,
    )

    match_score: Mapped[Decimal | None] = mapped_column(
        Numeric(5, 4),
        nullable=True,
    )

    price_source: Mapped[str] = mapped_column(
        String(40),
        nullable=False,
        default="unresolved",
    )

    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utcnow,
        server_default=func.now(),
    )

    invoice: Mapped[Invoice] = relationship(
        back_populates="items"
    )

    service: Mapped[Service | None] = relationship()


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        primary_key=True,
        default=uuid.uuid4,
    )

    invoice_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("invoices.id"),
        nullable=False,
    )

    event_type: Mapped[str] = mapped_column(
        String(80),
        nullable=False,
    )

    event_metadata: Mapped[dict | None] = mapped_column(
        "metadata",
        JSON,
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utcnow,
        server_default=func.now(),
    )

    invoice: Mapped[Invoice] = relationship(
        back_populates="audit_logs"
    )