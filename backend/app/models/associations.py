from sqlalchemy import Column, ForeignKey, Table, Uuid

from app.db.base import Base


usuario_rol = Table(
    "usuario_rol",
    Base.metadata,

    Column(
        "usuario_id",
        Uuid(as_uuid=True),
        ForeignKey("usuario.id", ondelete="CASCADE"),
        primary_key=True
    ),

    Column(
        "rol_id",
        Uuid(as_uuid=True),
        ForeignKey("rol.id", ondelete="CASCADE"),
        primary_key=True
    )
)