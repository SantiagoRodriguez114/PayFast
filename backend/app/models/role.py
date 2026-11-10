import uuid

from sqlalchemy import String, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.associations import usuario_rol


class Rol(Base):
    __tablename__ = "rol"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )

    nombre: Mapped[str] = mapped_column(
        String(30),
        unique=True,
        nullable=False
    )

    usuarios: Mapped[list["Usuario"]] = relationship(
        secondary=usuario_rol,
        back_populates="roles"
    )