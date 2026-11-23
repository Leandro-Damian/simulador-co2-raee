"""Motor de cálculo de CO₂ evitado.

Reglas anti doble contabilidad:
  1. Cada par (equipo/componente/fracción, id) se contabiliza una sola vez.
  2. Los componentes que pertenecen a un equipo incluido en el escenario se excluyen.
  3. Un ítem usa un único modo y una única vía de factor:
       - reutilización -> factor general/reutilización del peso total;
       - reciclaje de equipo -> se despliega su BOM y se aplica el factor de cada fracción;
       - reciclaje de componente/fracción -> factor de su fracción;
       - sin recuperación -> 0 kg CO₂e.
  4. Las fracciones sueltas se cuentan solo si se cargan como ítems independientes;
     el sistema avisa cuando además hay equipos (cuya BOM ya fue contabilizada).
"""

from __future__ import annotations

import json
from collections import defaultdict

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Component, Equivalence, EquipmentModel, Factor, Fraction, Scenario
from app.schemas.calculation import (
    BreakdownLine,
    CalculationLine,
    CalculationResult,
    CalculationTotals,
    CalculateItemIn,
    CalculateRequest,
    EquivalenceResult,
)
from app.services.formatting import format_equivalence

MODE_LABELS = {
    "reuse": "Reutilización / reacondicionamiento",
    "recycling": "Reciclaje / valorización",
    "no_recovery": "Sin recuperación",
}

FALLBACK_REUSE = "default_reuse"
FALLBACK_RECYCLING = "default_recycling"
NO_RECOVERY = "default_no_recovery"


class CalculationError(ValueError):
    """Entidad referenciada no encontrada o datos insuficientes."""


def _items_from_scenario(db: Session, scenario_id: int) -> list[CalculateItemIn]:
    scenario = db.get(Scenario, scenario_id)
    if scenario is None:
        raise CalculationError(f"No existe el escenario #{scenario_id}.")
    items: list[CalculateItemIn] = []
    for row in scenario.items:
        if row.equipment_model_id is not None:
            kind, entity_id = "equipment", row.equipment_model_id
        elif row.component_id is not None:
            kind, entity_id = "component", row.component_id
        elif row.fraction_id is not None:
            kind, entity_id = "fraction", row.fraction_id
        else:
            continue
        mode = row.mode or scenario.default_mode
        if mode not in MODE_LABELS:
            mode = scenario.default_mode if scenario.default_mode in MODE_LABELS else "reuse"
        attributes = json.loads(row.attributes_json) if row.attributes_json else None
        items.append(
            CalculateItemIn(
                kind=kind,
                id=entity_id,
                quantity=row.quantity,
                weight_kg=row.weight_kg,
                mode=mode,
                attributes=attributes,
            )
        )
    return items


def calculate(db: Session, request: CalculateRequest) -> CalculationResult:
    """Calcula el total estimado, el desglose y las equivalencias de un conjunto de ítems."""
    items = list(request.items)
    if not items and request.scenario_id is not None:
        items = _items_from_scenario(db, request.scenario_id)

    # Un escenario guardado se recalcula con el conjunto de factores que tenía
    # cuando se creó, incluidos los que después se dieron de baja. Así, activar o
    # desactivar materiales no cambia retroactivamente los históricos.
    # Las estimaciones nuevas (calculadora / escenarios sin guardar) usan solo
    # factores activos.
    is_historical = request.scenario_id is not None
    factor_stmt = select(Factor)
    if not is_historical:
        factor_stmt = factor_stmt.where(Factor.active.is_(True))
    factors = {
        factor.key: factor for factor in db.scalars(factor_stmt).all()
    }
    equivalences = db.scalars(
        select(Equivalence).where(Equivalence.active.is_(True)).order_by(Equivalence.id)
    ).all()

    warnings: list[str] = []
    lines: list[CalculationLine] = []
    seen: set[tuple[str, int]] = set()

    component_ids = {item.id for item in items if item.kind == "component"}
    equipment_ids = {item.id for item in items if item.kind == "equipment"}
    components_by_id: dict[int, Component] = (
        {
            component.id: component
            for component in db.scalars(
                select(Component).where(Component.id.in_(component_ids))
            ).all()
        }
        if component_ids
        else {}
    )

    def factor_value(key: str) -> float:
        factor = factors.get(key)
        if factor is None:
            warnings.append(
                f"Factor '{key}' no disponible (inactivo o eliminado): se aplicó 0 kg CO₂e/kg."
            )
            return 0.0
        return factor.value

    for item in items:
        identity = (item.kind, item.id)
        if identity in seen:
            warnings.append(
                f"Ítem duplicado ({item.kind} #{item.id}): se contabilizó una sola vez."
            )
            continue
        seen.add(identity)

        if item.kind == "equipment":
            entity = db.get(EquipmentModel, item.id)
            if entity is None:
                raise CalculationError(f"No existe el equipo #{item.id}.")
            brand = entity.brand.name if entity.brand else ""
            label = f"{brand} {entity.name}".strip()
            fallback_weight = entity.typical_weight_kg
            fraction = None
            subcategory_factor_key = (
                entity.subcategory.factor.key
                if entity.subcategory is not None and entity.subcategory.factor is not None
                else None
            )
        elif item.kind == "component":
            entity = components_by_id.get(item.id) or db.get(Component, item.id)
            if entity is None:
                raise CalculationError(f"No existe el componente #{item.id}.")
            label = entity.name
            fallback_weight = entity.weight_kg
            fraction = entity.fraction
            subcategory_factor_key = None
        else:
            entity = db.get(Fraction, item.id)
            if entity is None:
                raise CalculationError(f"No existe la fracción #{item.id}.")
            label = f"{entity.name} (fracción)"
            fallback_weight = 0.0
            fraction = entity
            subcategory_factor_key = None

        weight_each = item.weight_kg if item.weight_kg else fallback_weight
        total_weight = item.quantity * weight_each

        if item.kind == "component" and entity.equipment_model_id in equipment_ids:
            owner = db.get(EquipmentModel, entity.equipment_model_id)
            owner_name = owner.name if owner else f"#{entity.equipment_model_id}"
            reason = f"Ya contabilizado dentro del equipo {owner_name}."
            lines.append(
                CalculationLine(
                    label=label,
                    kind=item.kind,
                    mode=item.mode,
                    mode_label=MODE_LABELS[item.mode],
                    quantity=item.quantity,
                    weight_kg=round(total_weight, 4),
                    factor_key="none",
                    factor_value=0.0,
                    factor_unit="kg CO₂e/kg",
                    co2_kg=0.0,
                    excluded_reason=reason,
                )
            )
            warnings.append(f"{label}: {reason} No se suma por segunda vez.")
            continue

        if total_weight <= 0:
            warnings.append(
                f"{label}: no hay peso utilizable (informe weight_kg o use el peso por defecto). Se registró 0 kg CO₂e."
            )
            lines.append(
                CalculationLine(
                    label=label,
                    kind=item.kind,
                    mode=item.mode,
                    mode_label=MODE_LABELS[item.mode],
                    quantity=item.quantity,
                    weight_kg=0.0,
                    factor_key="none",
                    factor_value=0.0,
                    factor_unit="kg CO₂e/kg",
                    co2_kg=0.0,
                    excluded_reason="Sin peso",
                )
            )
            continue

        breakdown: list[BreakdownLine] | None = None

        if item.mode == "no_recovery":
            factor_key, factor_value_used, co2 = NO_RECOVERY, 0.0, 0.0

        elif item.mode == "reuse":
            if item.kind == "fraction":
                factor_key, factor_value_used, co2 = FALLBACK_REUSE, 0.0, 0.0
                warnings.append(
                    f"{label}: las fracciones materiales no se reutilizan; se registraron 0 kg CO₂e. Use reciclaje/valorización."
                )
            else:
                factor_key = subcategory_factor_key or FALLBACK_REUSE
                factor_value_used = factor_value(factor_key)
                co2 = total_weight * factor_value_used

        else:  # recycling
            if item.kind == "equipment":
                bom: list[tuple[str, float, str]] = []
                for component in entity.components:
                    component_weight = component.weight_kg * component.quantity
                    component_factor_key = (
                        component.fraction.factor.key
                        if component.fraction is not None and component.fraction.factor is not None
                        else FALLBACK_RECYCLING
                    )
                    bom.append(
                        (
                            component_factor_key,
                            component_weight,
                            component.fraction.name if component.fraction else "Sin fracción",
                        )
                    )
                bom_total = sum(weight for _, weight, _ in bom)
                if bom_total > 0:
                    scale = total_weight / bom_total
                    aggregated: dict[str, float] = defaultdict(float)
                    breakdown = []
                    for key_name, weight, fraction_label in bom:
                        scaled_weight = weight * scale
                        value = factor_value(key_name)
                        partial = scaled_weight * value
                        aggregated[key_name] += partial
                        breakdown.append(
                            BreakdownLine(
                                label=fraction_label,
                                factor_key=key_name,
                                weight_kg=round(scaled_weight, 4),
                                factor_value=value,
                                co2_kg=round(partial, 4),
                            )
                        )
                    co2 = sum(aggregated.values())
                    factor_key = "bom_fractions"
                    factor_value_used = co2 / total_weight
                else:
                    factor_key = FALLBACK_RECYCLING
                    factor_value_used = factor_value(factor_key)
                    co2 = total_weight * factor_value_used
            else:
                factor_key = (
                    fraction.factor.key
                    if fraction is not None and fraction.factor is not None
                    else FALLBACK_RECYCLING
                )
                factor_value_used = factor_value(factor_key)
                co2 = total_weight * factor_value_used

        lines.append(
            CalculationLine(
                label=label,
                kind=item.kind,
                mode=item.mode,
                mode_label=MODE_LABELS[item.mode],
                quantity=item.quantity,
                weight_kg=round(total_weight, 4),
                factor_key=factor_key,
                factor_value=round(factor_value_used, 6),
                factor_unit="kg CO₂e/kg",
                co2_kg=round(co2, 4),
                breakdown=breakdown,
            )
        )

    fraction_ids = {item.id for item in items if item.kind == "fraction"}
    if equipment_ids and fraction_ids:
        warnings.append(
            "El escenario combina equipos y fracciones sueltas: la BOM de los equipos ya se contabilizó. "
            "No vuelva a cargar esas fracciones como ítems independientes."
        )

    def sum_mode(mode: str) -> float:
        return round(
            sum(line.co2_kg for line in lines if line.mode == mode and not line.excluded_reason),
            4,
        )

    totals = CalculationTotals(
        total_weight_kg=round(
            sum(line.weight_kg for line in lines if not line.excluded_reason), 4
        ),
        co2_reuse=sum_mode("reuse"),
        co2_recycling=sum_mode("recycling"),
        co2_no_recovery=sum_mode("no_recovery"),
        co2_total=round(sum(line.co2_kg for line in lines if not line.excluded_reason), 4),
    )

    equivalence_results = [
        EquivalenceResult(
            label=equivalence.label,
            value=round(totals.co2_total * equivalence.value, 4),
            display=format_equivalence(equivalence.label, totals.co2_total * equivalence.value),
            unit=equivalence.unit,
            note=equivalence.note,
        )
        for equivalence in equivalences
    ]

    return CalculationResult(
        lines=lines,
        totals=totals,
        equivalences=equivalence_results,
        warnings=warnings,
    )
