from __future__ import annotations

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

import app  # noqa: F401  (necesario para resolver anotaciones totalmente cualificadas)
from app.core.database import Base
from app.models.factors import Factor


class Fraction(Base):
    """Fracción clasificada por peso. Referencia opcional a su Factor por defecto."""

    __tablename__ = "fractions"
    __table_args__ = (
        CheckConstraint("type IN ('metal','plastic','other')", name="ck_fraction_type"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(80), unique=True, nullable=False)
    type: Mapped[str] = mapped_column(String(20), nullable=False, default="other")
    color: Mapped[str | None] = mapped_column(String(20), nullable=True)
    factor_id: Mapped[int | None] = mapped_column(
        ForeignKey("factors.id", ondelete="SET NULL"), nullable=True
    )
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    # Baja lógica: permite quitar un material del alta sin romper escenarios
    # históricos ni componentes que todavía lo referencian.
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    factor: Mapped[Factor | None] = relationship()
    components: Mapped[list[Component]] = relationship(back_populates="fraction")


class Component(Base):
    """Componente suelto o ítem de la BOM de un equipo.

    equipment_model_id nullable=True:
      - con valor -> componente perteneciente a la BOM del equipo;
      - sin valor -> componente suelto (p. ej. memoria RAM o fuente suelta).
    parent_id permite BOM anidada (subcomponentes).
    """

    __tablename__ = "components"
    __table_args__ = (
        UniqueConstraint("equipment_model_id", "name", name="uq_component_in_equipment"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    equipment_model_id: Mapped[int | None] = mapped_column(
        ForeignKey("equipment_models.id", ondelete="SET NULL"), nullable=True
    )
    parent_id: Mapped[int | None] = mapped_column(
        ForeignKey("components.id", ondelete="SET NULL"), nullable=True
    )
    fraction_id: Mapped[int | None] = mapped_column(
        ForeignKey("fractions.id", ondelete="SET NULL"), nullable=True
    )
    weight_kg: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    equipment_model: Mapped[app.models.catalog.EquipmentModel | None] = relationship(  # noqa: F821
        back_populates="components"
    )
    fraction: Mapped[Fraction | None] = relationship(back_populates="components")
    parent: Mapped[Component | None] = relationship(
        "Component", remote_side=[id], back_populates="children"
    )
    children: Mapped[list[Component]] = relationship(
        "Component", back_populates="parent", cascade="all, delete-orphan"
    )

    @property
    def is_loose(self) -> bool:
        """True cuando el componente no pertenece a ningún modelo de equipo."""
        return self.equipment_model_id is None
