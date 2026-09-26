"""add invoice settings snapshots

Revision ID: 0004_invoice_settings_snapshot
Revises: 0003_workspace_settings
"""

from alembic import op
import sqlalchemy as sa


revision = "0004_invoice_settings_snapshot"
down_revision = "0003_workspace_settings"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "invoices",
        sa.Column(
            "company_name_snapshot",
            sa.String(200),
            nullable=True,
        ),
    )

    op.add_column(
        "invoices",
        sa.Column(
            "company_email_snapshot",
            sa.String(255),
            nullable=True,
        ),
    )

    op.add_column(
        "invoices",
        sa.Column(
            "company_address_snapshot",
            sa.Text(),
            nullable=True,
        ),
    )

    op.add_column(
        "invoices",
        sa.Column(
            "payment_information_snapshot",
            sa.Text(),
            nullable=True,
        ),
    )

    op.add_column(
        "invoices",
        sa.Column(
            "tax_enabled_snapshot",
            sa.Boolean(),
            nullable=True,
        ),
    )

    op.add_column(
        "invoices",
        sa.Column(
            "tax_type_snapshot",
            sa.String(30),
            nullable=True,
        ),
    )

    op.add_column(
        "invoices",
        sa.Column(
            "gstin_snapshot",
            sa.String(30),
            nullable=True,
        ),
    )

    op.add_column(
        "invoices",
        sa.Column(
            "business_state_snapshot",
            sa.String(100),
            nullable=True,
        ),
    )


def downgrade() -> None:
    op.drop_column(
        "invoices",
        "business_state_snapshot",
    )

    op.drop_column(
        "invoices",
        "gstin_snapshot",
    )

    op.drop_column(
        "invoices",
        "tax_type_snapshot",
    )

    op.drop_column(
        "invoices",
        "tax_enabled_snapshot",
    )

    op.drop_column(
        "invoices",
        "payment_information_snapshot",
    )

    op.drop_column(
        "invoices",
        "company_address_snapshot",
    )

    op.drop_column(
        "invoices",
        "company_email_snapshot",
    )

    op.drop_column(
        "invoices",
        "company_name_snapshot",
    )