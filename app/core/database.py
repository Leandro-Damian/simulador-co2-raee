from __future__ import annotations

from collections.abc import Generator

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.config import get_settings

settings = get_settings()

engine = create_engine(
    settings.database_url,
    connect_args={"check_same_thread": False},
    echo=settings.debug,
)

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    """Declarative base compartida por todos los modelos."""


def _ensure_fraction_active_column() -> None:
    """Migración mínima: agrega fractions.active en bases creadas antes del Bloque 4."""
    inspector = inspect(engine)
    if "fractions" not in inspector.get_table_names():
        return
    columns = {column["name"] for column in inspector.get_columns("fractions")}
    if "active" not in columns:
        with engine.begin() as connection:
            connection.execute(
                text("ALTER TABLE fractions ADD COLUMN active BOOLEAN NOT NULL DEFAULT 1")
            )


def init_db() -> None:
    """Crea el directorio de datos, las tablas y registra todos los mappers."""
    # Importar los modelos garantiza que estén en Base.metadata antes de create_all.
    from app import models  # noqa: F401

    Base.metadata.create_all(bind=engine)
    _ensure_fraction_active_column()


def get_db() -> Generator[Session, None, None]:
    """Dependencia FastAPI: entrega una sesión y siempre la cierra."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
