"""CRUD de escenarios/lotes guardados y cálculo asociado."""

from __future__ import annotations

import json

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models import Component, EquipmentModel, Fraction, Scenario, ScenarioItem
from app.schemas import (
    CalculateRequest,
    CalculationResult,
    ScenarioItemOut,
    ScenarioOut,
    ScenarioPayload,
)
from app.services import CalculationError, calculate

router = APIRouter(prefix="/api/scenarios", tags=["Escenarios"])


def _error(status_code: int, detail: str) -> None:
    raise HTTPException(status_code=status_code, detail=detail)


def _get_scenario(db: Session, scenario_id: int) -> Scenario:
    scenario = db.get(Scenario, scenario_id)
    if scenario is None:
        _error(404, f"No existe el escenario #{scenario_id}.")
    return scenario


def _entity_label(db: Session, kind: str, entity_id: int) -> str:
    if kind == "equipment":
        entity = db.get(EquipmentModel, entity_id)
        if entity is None:
            _error(400, f"No existe el equipo #{entity_id}.")
        brand = entity.brand.name if entity.brand else ""
        return f"{brand} {entity.name}".strip()
    if kind == "component":
        entity = db.get(Component, entity_id)
        if entity is None:
            _error(400, f"No existe el componente #{entity_id}.")
        return entity.name
    entity = db.get(Fraction, entity_id)
    if entity is None:
        _error(400, f"No existe la fracción #{entity_id}.")
    return f"{entity.name} (fracción)"


def _item_tuple(row: ScenarioItem) -> tuple[str, int]:
    if row.equipment_model_id is not None:
        return "equipment", row.equipment_model_id
    if row.component_id is not None:
        return "component", row.component_id
    if row.fraction_id is not None:
        return "fraction", row.fraction_id
    return "fraction", 0


def _scenario_out(db: Session, scenario: Scenario) -> ScenarioOut:
    items: list[ScenarioItemOut] = []
    for row in scenario.items:
        kind, entity_id = _item_tuple(row)
        label = (
            _entity_label(db, kind, entity_id)
            if entity_id
            else "Ítem incompleto (entidad eliminada)"
        )
        attributes = json.loads(row.attributes_json) if row.attributes_json else {}
        items.append(
            ScenarioItemOut(
                id=row.id,
                kind=kind,
                entity_id=entity_id,
                entity_label=label,
                quantity=row.quantity,
                weight_kg=row.weight_kg,
                mode=row.mode,
                attributes=attributes,
            )
        )
    total = 0.0
    if scenario.items:
        try:
            total = calculate(db, CalculateRequest(scenario_id=scenario.id)).totals.co2_total
        except CalculationError:
            total = 0.0
    return ScenarioOut(
        id=scenario.id,
        name=scenario.name,
        created_at=scenario.created_at,
        default_mode=scenario.default_mode,
        notes=scenario.notes,
        items=items,
        total_co2_kg=total,
    )


def _replace_items(db: Session, scenario: Scenario, items) -> None:
    for existing in list(scenario.items):
        db.delete(existing)
    db.flush()
    for item in items:
        _entity_label(db, item.kind, item.entity_id)  # validación
        attributes = (
            json.dumps(item.attributes, ensure_ascii=False) if item.attributes else None
        )
        db.add(
            ScenarioItem(
                scenario_id=scenario.id,
                equipment_model_id=item.entity_id if item.kind == "equipment" else None,
                component_id=item.entity_id if item.kind == "component" else None,
                fraction_id=item.entity_id if item.kind == "fraction" else None,
                quantity=item.quantity,
                weight_kg=item.weight_kg,
                mode=item.mode or scenario.default_mode,
                attributes_json=attributes,
            )
        )
    db.flush()


@router.get("", response_model=list[ScenarioOut])
def list_scenarios(db: Session = Depends(get_db)) -> list[ScenarioOut]:
    scenarios = db.scalars(
        select(Scenario).order_by(Scenario.created_at.desc(), Scenario.id.desc())
    ).all()
    return [_scenario_out(db, scenario) for scenario in scenarios]


@router.post("", response_model=ScenarioOut, status_code=status.HTTP_201_CREATED)
def create_scenario(payload: ScenarioPayload, db: Session = Depends(get_db)) -> ScenarioOut:
    scenario = Scenario(
        name=payload.name,
        default_mode=payload.default_mode,
        notes=payload.notes,
    )
    db.add(scenario)
    db.flush()
    _replace_items(db, scenario, payload.items)
    db.commit()
    db.refresh(scenario)  # recarga la relationship items antes de calcular el total
    return _scenario_out(db, scenario)


@router.get("/{scenario_id}", response_model=ScenarioOut)
def get_scenario(scenario_id: int, db: Session = Depends(get_db)) -> ScenarioOut:
    return _scenario_out(db, _get_scenario(db, scenario_id))


@router.put("/{scenario_id}", response_model=ScenarioOut)
def update_scenario(
    scenario_id: int, payload: ScenarioPayload, db: Session = Depends(get_db)
) -> ScenarioOut:
    scenario = _get_scenario(db, scenario_id)
    scenario.name = payload.name
    scenario.default_mode = payload.default_mode
    scenario.notes = payload.notes
    _replace_items(db, scenario, payload.items)
    db.commit()
    db.refresh(scenario)  # recarga la relationship items antes de calcular el total
    return _scenario_out(db, scenario)


@router.post("/{scenario_id}/duplicate", response_model=ScenarioOut, status_code=status.HTTP_201_CREATED)
def duplicate_scenario(scenario_id: int, db: Session = Depends(get_db)) -> ScenarioOut:
    source = _get_scenario(db, scenario_id)
    copy = Scenario(
        name=f"{source.name} (copia)",
        default_mode=source.default_mode,
        notes=source.notes,
    )
    db.add(copy)
    db.flush()
    for row in source.items:
        kind, entity_id = _item_tuple(row)
        if not entity_id:
            continue
        db.add(
            ScenarioItem(
                scenario_id=copy.id,
                equipment_model_id=entity_id if kind == "equipment" else None,
                component_id=entity_id if kind == "component" else None,
                fraction_id=entity_id if kind == "fraction" else None,
                quantity=row.quantity,
                weight_kg=row.weight_kg,
                mode=row.mode,
                attributes_json=row.attributes_json,
            )
        )
    db.commit()
    db.refresh(copy)  # recarga la relationship items antes de calcular el total
    return _scenario_out(db, copy)


@router.delete("/{scenario_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_scenario(scenario_id: int, db: Session = Depends(get_db)) -> None:
    scenario = _get_scenario(db, scenario_id)
    db.delete(scenario)
    db.commit()


@router.post("/{scenario_id}/calculate", response_model=CalculationResult)
def calculate_scenario(scenario_id: int, db: Session = Depends(get_db)) -> CalculationResult:
    _get_scenario(db, scenario_id)
    try:
        return calculate(db, CalculateRequest(scenario_id=scenario_id))
    except CalculationError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
