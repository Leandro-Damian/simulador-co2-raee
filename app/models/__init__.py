"""Registro central de modelos SQLAlchemy.

Importar este paquete garantiza que todas las tablas estén en Base.metadata.
"""

from app.models.catalog import (
    AttributeDef,
    AttributeValue,
    Brand,
    Category,
    EquipmentModel,
    Subcategory,
)
from app.models.factors import Equivalence, Factor
from app.models.fractions import Component, Fraction
from app.models.meta import SeedMeta
from app.models.rules import AcceptanceRule
from app.models.simulation import Scenario, ScenarioItem

__all__ = [
    "AcceptanceRule",
    "AttributeDef",
    "AttributeValue",
    "Brand",
    "Category",
    "Component",
    "Equivalence",
    "EquipmentModel",
    "Factor",
    "Fraction",
    "Scenario",
    "ScenarioItem",
    "SeedMeta",
    "Subcategory",
]
