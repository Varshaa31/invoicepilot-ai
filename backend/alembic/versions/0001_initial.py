"""initial schema

Revision ID: 0001_initial
Revises:
Create Date: 2026-09-24
"""

from alembic import op
import sqlalchemy as sa

revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("email", sa.String(255), nullable=False, unique=True),
        sa.Column("workspace_name", sa.String(120), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_table(
        "customers",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("email", sa.String(255), nullable=True),
        sa.Column("phone", sa.String(50), nullable=True),
        sa.Column("company", sa.String(200), nullable=True),
        sa.Column("address", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_table(
        "services",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("code", sa.String(40), nullable=False, unique=True),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("unit", sa.String(40), nullable=False),
        sa.Column("price", sa.Numeric(12, 2), nullable=False),
        sa.Column("currency", sa.String(8), nullable=False),
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_table(
        "service_aliases",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("service_id", sa.Uuid(), sa.ForeignKey("services.id"), nullable=False),
        sa.Column("alias", sa.String(200), nullable=False),
        sa.UniqueConstraint("service_id", "alias", name="uq_service_alias"),
    )
    op.create_table(
        "invoices",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("invoice_number", sa.String(40), nullable=False, unique=True),
        sa.Column("customer_id", sa.Uuid(), sa.ForeignKey("customers.id"), nullable=False),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("currency", sa.String(8), nullable=False),
        sa.Column("subtotal", sa.Numeric(12, 2), nullable=False),
        sa.Column("tax_rate", sa.Numeric(7, 4), nullable=False),
        sa.Column("tax_amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("total", sa.Numeric(12, 2), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("source_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("exported_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_table(
        "invoice_items",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("invoice_id", sa.Uuid(), sa.ForeignKey("invoices.id"), nullable=False),
        sa.Column("service_id", sa.Uuid(), sa.ForeignKey("services.id"), nullable=True),
        sa.Column("requested_service", sa.String(300), nullable=False),
        sa.Column("service_name_snapshot", sa.String(200), nullable=True),
        sa.Column("quantity", sa.Numeric(12, 2), nullable=False),
        sa.Column("unit_price", sa.Numeric(12, 2), nullable=True),
        sa.Column("line_total", sa.Numeric(12, 2), nullable=True),
        sa.Column("resolution_status", sa.String(32), nullable=False),
        sa.Column("match_score", sa.Numeric(5, 4), nullable=True),
        sa.Column("price_source", sa.String(40), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_table(
        "audit_logs",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("invoice_id", sa.Uuid(), sa.ForeignKey("invoices.id"), nullable=False),
        sa.Column("event_type", sa.String(80), nullable=False),
        sa.Column("metadata", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("audit_logs")
    op.drop_table("invoice_items")
    op.drop_table("invoices")
    op.drop_table("service_aliases")
    op.drop_table("services")
    op.drop_table("customers")
    op.drop_table("users")
