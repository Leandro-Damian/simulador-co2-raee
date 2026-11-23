from __future__ import annotations

from sqlalchemy import Boolean, CheckConstraint, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class AcceptanceRule(Base):
    """Regla de recepción: reject (no se recibe), warn (advertencia) o accept.

    `pattern` admite varias palabras clave separadas por '|'.
    `applies_to` es un código de categoría o 'all' para todas.
    """

    __tablename__ = "acceptance_rules"
    __table_args__ = (
        CheckConstraint("action IN ('reject','warn','accept')", name="ck_rule_action"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(160), nullable=False, unique=True)
    action: Mapped[str] = mapped_column(String(10), nullable=False)
    pattern: Mapped[str] = mapped_column(Text, nullable=False)
    applies_to: Mapped[str] = mapped_column(String(40), nullable=False, default="all")
    message: Mapped[str] = mapped_column(Text, nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
