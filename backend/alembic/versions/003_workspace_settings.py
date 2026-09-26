"""add workspace invoice and tax settings

Revision ID: 0003_workspace_settings
Revises: 0002_authentication
"""

from alembic import op
import sqlalchemy as sa


revision = "0003_workspace_settings"
down_revision = "0002_authentication"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "workspace_settings",
        sa.Column(
            "id",
            sa.Uuid(),
            primary_key=True,
        ),
        sa.Column(
            "user_id",
            sa.Uuid(),
            sa.ForeignKey(
                "users.id",
                ondelete="CASCADE",
            ),
            nullable=False,
            unique=True,
        ),
        sa.Column(
            "company_name",
            sa.String(200),
            nullable=False,
            server_default="InvoicePilot AI",
        ),
        sa.Column(
            "company_email",
            sa.String(255),
            nullable=False,
            server_default="billing@invoicepilot.demo",
        ),
        sa.Column(
            "company_address",
            sa.Text(),
            nullable=False,
            server_default="Bengaluru, India",
        ),
        sa.Column(
            "payment_information",
            sa.Text(),
            nullable=False,
            server_default=(
                "Bank transfer · A/C InvoicePilot AI · "
                "IFSC DEMO0001234"
            ),
        ),
        sa.Column(
            "default_currency",
            sa.String(8),
            nullable=False,
            server_default="INR",
        ),
        sa.Column(
            "tax_enabled",
            sa.Boolean(),
            nullable=False,
            server_default=sa.true(),
        ),
        sa.Column(
            "tax_type",
            sa.String(30),
            nullable=False,
            server_default="GST",
        ),
        sa.Column(
            "default_tax_rate",
            sa.Numeric(7, 4),
            nullable=False,
            server_default="18.00",
        ),
        sa.Column(
            "gstin",
            sa.String(30),
            nullable=True,
        ),
        sa.Column(
            "business_state",
            sa.String(100),
            nullable=True,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )


def downgrade() -> None:
    op.drop_table("workspace_settings")