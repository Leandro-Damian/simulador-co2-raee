from __future__ import annotations

from sqlalchemy import ForeignKey, Index, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.factors import Factor


class Category(Base):
    """Categoría RAEE de primer nivel (p. ej. Informática y oficina)."""

    __tablename__ = "categories"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)
    code: Mapped[str] = mapped_column(String(40), unique=True, nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    subcategories: Mapped[list[Subcategory]] = relationship(
        back_populates="category", cascade="all, delete-orphan"
    )


class Subcategory(Base):
    """Subcategoría editable. Referencia opcional a un Factor para el cálculo del Bloque 2."""

    __tablename__ = "subcategories"
    __table_args__ = (
        UniqueConstraint("category_id", "name", name="uq_subcategory_category_name"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    category_id: Mapped[int] = mapped_column(
        ForeignKey("categories.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(140), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    factor_id: Mapped[int | None] = mapped_column(
        ForeignKey("factors.id", ondelete="SET NULL"), nullable=True
    )
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    category: Mapped[Category] = relationship(back_populates="subcategories")
    factor: Mapped[Factor | None] = relationship()  # noqa: F821
    equipment_models: Mapped[list[EquipmentModel]] = relationship(
        back_populates="subcategory"
    )


class Brand(Base):
    __tablename__ = "brands"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)

    equipment_models: Mapped[list[EquipmentModel]] = relationship(back_populates="brand")


class EquipmentModel(Base):
    """Modelo de equipo (p. ej. Lenovo ThinkCentre M82 SFF)."""

    __tablename__ = "equipment_models"
    __table_args__ = (
        UniqueConstraint("subcategory_id", "brand_id", "name", name="uq_equipment_model"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    subcategory_id: Mapped[int] = mapped_column(
        ForeignKey("subcategories.id", ondelete="RESTRICT"), nullable=False
    )
    brand_id: Mapped[int | None] = mapped_column(
        ForeignKey("brands.id", ondelete="SET NULL"), nullable=True
    )
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    typical_weight_kg: Mapped[float] = mapped_column(nullable=False, default=0.0)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    subcategory: Mapped[Subcategory] = relationship(back_populates="equipment_models")
    brand: Mapped[Brand | None] = relationship(back_populates="equipment_models")
    components: Mapped[list[Component]] = relationship(  # noqa: F821
        back_populates="equipment_model", cascade="all, delete-orphan"
    )


class AttributeDef(Base):
    """Definición de atributo técnico variable por equipo o componente."""

    __tablename__ = "attribute_defs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)
    data_type: Mapped[str] = mapped_column(String(20), nullable=False, default="text")
    unit: Mapped[str | None] = mapped_column(String(30), nullable=True)
    options_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    scope: Mapped[str] = mapped_column(String(20), nullable=False, default="component")
    is_active: Mapped[bool] = mapped_column(nullable=False, default=True)

    values: Mapped[list[AttributeValue]] = relationship(  # noqa: F821
        back_populates="definition", cascade="all, delete-orphan"
    )


class AttributeValue(Base):
    """Valor polimórfico: entity_type es equipment_model | component | scenario_item."""

    __tablename__ = "attribute_values"
    __table_args__ = (Index("ix_attribute_values_entity", "entity_type", "entity_id"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    definition_id: Mapped[int] = mapped_column(
        ForeignKey("attribute_defs.id", ondelete="CASCADE"), nullable=False
    )
    entity_type: Mapped[str] = mapped_column(String(30), nullable=False)
    entity_id: Mapped[int] = mapped_column(Integer, nullable=False)
    value: Mapped[str] = mapped_column(Text, nullable=False)

    definition: Mapped[AttributeDef] = relationship(back_populates="values")


# Import al final para evitar el ciclo catalog <-> fractions. Se resuelve al
# configurar los mappers (init_db importa todos los modelos antes de create_all).
from app.models.fractions import Component  # noqa: E402,F401
