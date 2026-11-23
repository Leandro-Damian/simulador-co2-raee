from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import JSONResponse
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.core.database import get_db
from app.models import Component, Equivalence, EquipmentModel, Factor, Fraction
from app.schemas import (
    CalculateRequest,
    CalculationResult,
    EquivalenceOut,
    EquivalenceUpdate,
    FactorCreate,
    FactorOut,
    FactorUpdate,
)
from app.services import CalculationError, calculate

router = APIRouter(prefix="/api", tags=["API"])
logger = logging.getLogger(__name__)


@router.get("/factors", response_model=list[FactorOut])
def list_factors(
    mode: str | None = Query(default=None),
    active_only: bool = Query(default=False),
    db: Session = Depends(get_db),
) -> list[FactorOut]:
    stmt = select(Factor)
    if mode:
        stmt = stmt.where(Factor.mode == mode)
    if active_only:
        stmt = stmt.where(Factor.active.is_(True))
    return list(db.scalars(stmt.order_by(Factor.mode, Factor.key)).all())


@router.post("/factors", response_model=FactorOut, status_code=status.HTTP_201_CREATED)
def create_factor(payload: FactorCreate, db: Session = Depends(get_db)) -> FactorOut:
    exists = db.scalar(select(Factor).where(Factor.key == payload.key))
    if exists is not None:
        raise HTTPException(status_code=409, detail=f"Ya existe el factor con clave '{payload.key}'.")
    factor = Factor(**payload.model_dump())
    db.add(factor)
    db.commit()
    db.refresh(factor)
    return factor


@router.put("/factors/{factor_id}", response_model=FactorOut)
def update_factor(factor_id: int, payload: FactorUpdate, db: Session = Depends(get_db)) -> FactorOut:
    factor = db.get(Factor, factor_id)
    if factor is None:
        raise HTTPException(status_code=404, detail="Factor no encontrado.")
    for attribute, value in payload.model_dump(exclude_unset=True).items():
        setattr(factor, attribute, value)
    db.commit()
    db.refresh(factor)
    return factor


@router.delete("/factors/{factor_id}", response_model=FactorOut)
def deactivate_factor(factor_id: int, db: Session = Depends(get_db)) -> FactorOut:
    """Baja lógica: mantiene las referencias históricas de fracciones y subcategorías."""
    factor = db.get(Factor, factor_id)
    if factor is None:
        raise HTTPException(status_code=404, detail="Factor no encontrado.")
    factor.active = False
    db.commit()
    db.refresh(factor)
    return factor


@router.post("/factors/{factor_id}/activate", response_model=FactorOut)
def activate_factor(factor_id: int, db: Session = Depends(get_db)) -> FactorOut:
    """Reactiva un factor dado de baja; no altera su valor editable."""
    factor = db.get(Factor, factor_id)
    if factor is None:
        raise HTTPException(status_code=404, detail="Factor no encontrado.")
    factor.active = True
    db.commit()
    db.refresh(factor)
    return factor


@router.get("/equivalences", response_model=list[EquivalenceOut])
def list_equivalences(db: Session = Depends(get_db)) -> list[EquivalenceOut]:
    return list(db.scalars(select(Equivalence).order_by(Equivalence.id)).all())


@router.put("/equivalences/{equivalence_id}", response_model=EquivalenceOut)
def update_equivalence(
    equivalence_id: int, payload: EquivalenceUpdate, db: Session = Depends(get_db)
) -> EquivalenceOut:
    equivalence = db.get(Equivalence, equivalence_id)
    if equivalence is None:
        raise HTTPException(status_code=404, detail="Equivalencia no encontrada.")
    for attribute, value in payload.model_dump(exclude_unset=True).items():
        setattr(equivalence, attribute, value)
    db.commit()
    db.refresh(equivalence)
    return equivalence


@router.get("/catalog/options")
def catalog_options(db: Session = Depends(get_db)) -> dict:
    """Opciones livianas para el simulador y la calculadora rápida."""
    equipment_models = db.scalars(
        select(EquipmentModel).options(selectinload(EquipmentModel.brand)).order_by(EquipmentModel.name)
    ).all()
    components = db.scalars(
        select(Component)
        .options(selectinload(Component.fraction))
        .order_by(Component.name)
    ).all()
    fractions = db.scalars(
        select(Fraction)
        .where(Fraction.active.is_(True))
        .order_by(Fraction.sort_order, Fraction.name)
    ).all()

    return {
        "equipment": [
            {
                "id": item.id,
                "label": f"{item.brand.name} {item.name}".strip() if item.brand else item.name,
                "name": item.name,
                "weight_kg": item.typical_weight_kg,
            }
            for item in equipment_models
        ],
        "components": [
            {
                "id": item.id,
                "label": item.name,
                "name": item.name,
                "is_loose": item.equipment_model_id is None,
                "weight_kg": item.weight_kg,
                "fraction": item.fraction.name if item.fraction else None,
            }
            for item in components
        ],
        "fractions": [
            {
                "id": item.id,
                "label": item.name,
                "name": item.name,
                "type": item.type,
                "color": item.color,
            }
            for item in fractions
        ],
        "modes": [
            {"value": "reuse", "label": "Reutilización / reacondicionamiento"},
            {"value": "recycling", "label": "Reciclaje / valorización"},
            {"value": "no_recovery", "label": "Sin recuperación"},
        ],
    }


@router.post("/calculate", response_model=CalculationResult)
def calculate_preview(payload: CalculateRequest, db: Session = Depends(get_db)) -> JSONResponse:
    """Estimación paramétrica: no persiste nada; la usan la calculadora y el simulador.

    Se devuelve un JSONResponse explícito para garantizar cuerpo y Content-Type,
    incluso con versiones nuevas de FastAPI donde la serialización del response_model
    podría omitir el body. Los errores inesperados también se responden como JSON,
    para que el cliente nunca reciba una respuesta vacía al hacer response.json().
    """
    try:
        result = calculate(db, payload)
        return JSONResponse(content=result.model_dump(mode="json"))
    except CalculationError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except Exception as exc:  # pragma: no cover - defensa ante datos inconsistentes
        logger.exception("Error inesperado al calcular la estimación")
        return JSONResponse(
            status_code=500,
            content={"detail": f"No se pudo calcular la estimación: {exc}"},
        )
