from sqlalchemy import select

from app.db.session import SessionLocal
from app.models import Rol


def inicializar_roles():
    roles_iniciales = ["emprendedor", "prestamista"]

    db = SessionLocal()

    try:
        roles_existentes = set(
            db.scalars(select(Rol.nombre)).all()
        )

        roles_creados = []

        for nombre in roles_iniciales:
            if nombre not in roles_existentes:
                db.add(Rol(nombre=nombre))
                roles_creados.append(nombre)

        if roles_creados:
            db.commit()
            print(f"Roles creados: {', '.join(roles_creados)}")
        else:
            print("Los roles iniciales ya existen.")

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


if __name__ == "__main__":
    inicializar_roles()
