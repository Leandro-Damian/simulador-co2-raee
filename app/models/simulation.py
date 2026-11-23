from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.catalog import EquipmentModel
from app.models.fractions import Fraction, Component


class Scenario(Base):
    """Escenario / lote guardado por la organización."""

    __tablename__ = "scenarios"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(180), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    default_mode: Mapped[str] = mapped_column(
        String(30), nullable=False, default="reuse"
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    items: Mapped[list[ScenarioItem]] = relationship(
        back_populates="scenario", cascade="all, delete-orphan"
    )


class ScenarioItem(Base):
    """Ítem de un escenario: puede asociar un equipo, un componente suelto o una fracción por peso."""

    __tablename__ = "scenario_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    scenario_id: Mapped[int] = mapped_column(
        ForeignKey("scenarios.id", ondelete="CASCADE"), nullable=False
    )
    equipment_model_id: Mapped[int | None] = mapped_column(
        ForeignKey("equipment_models.id", ondelete="SET NULL"), nullable=True
    )
    component_id: Mapped[int | None] = mapped_column(
        ForeignKey("components.id", ondelete="SET NULL"), nullable=True
    )
    fraction_id: Mapped[int | None] = mapped_column(
        ForeignKey("fractions.id", ondelete="SET NULL"), nullable=True
    )
    quantity: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    weight_kg: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    mode: Mapped[str | None] = mapped_column(String(30), nullable=True)
    attributes_json: Mapped[str | None] = mapped_column(Text, nullable=True)

    scenario: Mapped[Scenario] = relationship(back_populates="items")
    equipment_model: Mapped[EquipmentModel | None] = relationship()
    component: Mapped[Component | None] = relationship()
    fraction: Mapped[Fraction | None] = relationship()
