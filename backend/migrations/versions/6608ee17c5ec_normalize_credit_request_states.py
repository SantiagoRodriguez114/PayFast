"""normalize credit request states

Revision ID: 6608ee17c5ec
Revises: 3e2c9f8e8e9c
Create Date: 2026-11-15 22:13:11.356648

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '6608ee17c5ec'
down_revision: Union[str, Sequence[str], None] = '3e2c9f8e8e9c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Normalizar los estados iniciales que ya existen.
    op.execute(
        """
        UPDATE solicitud_credito
        SET estado = 'PENDIENTE_EVALUACION'
        WHERE estado = 'pendiente_evaluacion'
        """
    )

    # Usar batch_alter_table para compatibilidad con SQLite y PostgreSQL
    with op.batch_alter_table("solicitud_credito", schema=None) as batch_op:
        batch_op.alter_column(
            "estado",
            existing_type=sa.String(length=40),
            existing_nullable=False,
            server_default=sa.text("'PENDIENTE_EVALUACION'"),
        )


def downgrade() -> None:
    with op.batch_alter_table("solicitud_credito", schema=None) as batch_op:
        batch_op.alter_column(
            "estado",
            existing_type=sa.String(length=40),
            existing_nullable=False,
            server_default=sa.text("'pendiente_evaluacion'"),
        )

    op.execute(
        """
        UPDATE solicitud_credito
        SET estado = 'pendiente_evaluacion'
        WHERE estado = 'PENDIENTE_EVALUACION'
        """
    )