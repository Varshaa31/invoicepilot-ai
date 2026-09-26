"""add authentication and invoice ownership

Revision ID: 0002_authentication
Revises: 0001_initial
"""

from alembic import op
import sqlalchemy as sa


revision = "0002_authentication"
down_revision = "0001_initial"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Extend the existing users table for email/password authentication.
    op.add_column(
        "users",
        sa.Column(
            "password_hash",
            sa.String(255),
            nullable=True,
        ),
    )

    op.add_column(
        "users",
        sa.Column(
            "email_verified",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
    )

    # Link Google/Apple identities to an existing InvoicePilot user.
    op.create_table(
        "auth_accounts",
        sa.Column(
            "id",
            sa.Uuid(),
            primary_key=True,
        ),
        sa.Column(
            "user_id",
            sa.Uuid(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "provider",
            sa.String(40),
            nullable=False,
        ),
        sa.Column(
            "provider_account_id",
            sa.String(255),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.UniqueConstraint(
            "provider",
            "provider_account_id",
            name="uq_auth_account_provider",
        ),
    )

    # Associate invoices with the authenticated InvoicePilot user.
    # Nullable initially so existing invoices are not broken.
    op.add_column(
        "invoices",
        sa.Column(
            "user_id",
            sa.Uuid(),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )

    op.create_index(
        "ix_invoices_user_id",
        "invoices",
        ["user_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_invoices_user_id", table_name="invoices")

    op.drop_column("invoices", "user_id")

    op.drop_table("auth_accounts")

    op.drop_column("users", "email_verified")
    op.drop_column("users", "password_hash")