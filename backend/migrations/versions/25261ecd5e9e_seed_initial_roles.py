"""seed initial roles

Revision ID: 25261ecd5e9e
Revises: 54902da3d90e
Create Date: 2026-11-18 10:00:08.330058

"""
from typing import Sequence, Union

import uuid

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '25261ecd5e9e'
down_revision: Union[str, Sequence[str], None] = '54902da3d90e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Inicializa los roles que PayFast necesita para registrar usuarios.

    ON CONFLICT evita duplicar roles si ya existen en la base de datos.
    """
    connection = op.get_bind()

    for nombre in ("emprendedor", "prestamista", "admin"):
        connection.execute(
            sa.text("""
                INSERT INTO rol (id, nombre)
                VALUES (:id, :nombre)
                ON CONFLICT (nombre) DO NOTHING
            """),
            {
                "id": uuid.uuid4(),
                "nombre": nombre,
            },
        )


def downgrade() -> None:
    """
    No eliminamos los roles automáticamente porque podrían estar
    asociados a usuarios existentes.
    """
    pass