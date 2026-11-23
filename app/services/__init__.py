"""Servicios de negocio: cálculo de CO₂ evitado y formateo de equivalencias."""

from app.services.calculator import CalculationError, calculate
from app.services.formatting import format_equivalence, friendly_number

__all__ = ["CalculationError", "calculate", "format_equivalence", "friendly_number"]
