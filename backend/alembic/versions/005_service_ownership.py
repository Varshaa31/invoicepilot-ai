"""add service ownership

Revision ID: 0005_service_ownership
Revises: 0004_invoice_settings_snapshot
"""

from alembic import op
import sqlalchemy as sa


revision = "0005_service_ownership"
down_revision = "0004_invoice_settings_snapshot"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "services",
        sa.Column(
            "user_id",
            sa.Uuid(),
            nullable=True,
        ),
    )

    # Existing catalog records belong to the existing demo workspace.
    op.execute(
        """
        UPDATE services
        SET user_id = 'ecb933a4-bc13-4c27-8db9-fd79cf8d35a9'
        WHERE user_id IS NULL
        """
    )

    op.alter_column(
        "services",
        "user_id",
        nullable=False,
    )

    op.create_foreign_key(
        "fk_services_user_id_users",
        "services",
        "users",
        ["user_id"],
        ["id"],
        ondelete="CASCADE",
    )

    op.create_index(
        "ix_services_user_id",
        "services",
        ["user_id"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_services_user_id",
        table_name="services",
    )

    op.drop_constraint(
        "fk_services_user_id_users",
        "services",
        type_="foreignkey",
    )

    op.drop_column(
        "services",
        "user_id",
    )