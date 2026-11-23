from __future__ import annotations

from sqlalchemy import Boolean, CheckConstraint, Float, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Factor(Base):
    """Factor paramétrico editable desde el Panel de Factores y Referencias (Bloque 2)."""

    __tablename__ = "factors"
    __table_args__ = (
        CheckConstraint(
            "mode IN ('reuse','recycling','no_recovery','equivalence','material','all')",
            name="ck_factor_mode",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    key: Mapped[str] = mapped_column(String(80), unique=True, nullable=False, index=True)
    label: Mapped[str] = mapped_column(String(180), nullable=False)
    value: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    unit: Mapped[str] = mapped_column(String(40), nullable=False, default="kg CO₂e/kg")
    mode: Mapped[str] = mapped_column(String(30), nullable=False, default="all")
    source: Mapped[str | None] = mapped_column(Text, nullable=True)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)


class Equivalence(Base):
    """Equivalencia cotidiana escalable en el panel visual (Bloque 3)."""

    __tablename__ = "equivalences"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    label: Mapped[str] = mapped_column(String(180), nullable=False)
    value: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    unit: Mapped[str] = mapped_column(String(80), nullable=False)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
