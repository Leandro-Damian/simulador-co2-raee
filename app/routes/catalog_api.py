"""CRUD del catálogo extensible: categorías, marcas, modelos, atributos, BOM y fracciones."""

from __future__ import annotations

import json

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.core.database import get_db
from app.models import (
    AttributeDef,
    AttributeValue,
    Brand,
    Category,
    Component,
    EquipmentModel,
    Factor,
    Fraction,
    Subcategory,
)
from app.schemas import (
    AttributeDefIn,
    AttributeDefOut,
    BrandIn,
    BrandOut,
    CategoryIn,
    CategoryOut,
    ComponentIn,
    ComponentOut,
    EquipmentIn,
    EquipmentOut,
    FractionIn,
    FractionOut,
    SubcategoryIn,
    SubcategoryOut,
)

router = APIRouter(prefix="/api/catalog", tags=["Catálogo"])


def _error(status_code: int, detail: str) -> None:
    raise HTTPException(status_code=status_code, detail=detail)


def _get(db: Session, model: type, entity_id: int, label: str):
    entity = db.get(model, entity_id)
    if entity is None:
        _error(404, f"No existe {label} #{entity_id}.")
    return entity


def _attributes_for(db: Session, entity_type: str, entity_id: int) -> dict[str, str]:
    rows = db.scalars(
        select(AttributeValue)
        .join(AttributeDef)
        .where(
            AttributeValue.entity_type == entity_type,
            AttributeValue.entity_id == entity_id,
        )
    ).all()
    return {row.definition.name: row.value for row in rows}


def _sync_attributes(
    db: Session, entity_type: str, entity_id: int, values: dict[str, str]
) -> None:
    definitions = {definition.name: definition for definition in db.scalars(select(AttributeDef)).all()}
    by_id = {definition.id: definition for definition in definitions.values()}
    existing = db.scalars(
        select(AttributeValue).where(
            AttributeValue.entity_type == entity_type,
            AttributeValue.entity_id == entity_id,
        )
    ).all()
    by_definition = {value.definition_id: value for value in existing}

    for name, raw_value in values.items():
        definition = definitions.get(name)
        if definition is None:
            continue
        text = "" if raw_value is None else str(raw_value)
        if definition.id in by_definition:
            by_definition[definition.id].value = text
        else:
            db.add(
                AttributeValue(
                    definition_id=definition.id,
                    entity_type=entity_type,
                    entity_id=entity_id,
                    value=text,
                )
            )
    for definition_id, value in by_definition.items():
        definition = by_id.get(definition_id)
        if definition is None or definition.name not in values:
            db.delete(value)


def _delete_attributes(db: Session, entity_type: str, entity_id: int) -> None:
    for value in db.scalars(
        select(AttributeValue).where(
            AttributeValue.entity_type == entity_type,
            AttributeValue.entity_id == entity_id,
        )
    ).all():
        db.delete(value)


def _component_ids(db: Session, root_id: int) -> list[int]:
    """Incluye el componente y toda su descendencia (BOM anidada)."""
    ids = [root_id]
    cursor = 0
    while cursor < len(ids):
        children = db.scalars(
            select(Component.id).where(Component.parent_id == ids[cursor])
        ).all()
        ids.extend(child for child in children if child not in ids)
        cursor += 1
    return ids


def _component_out(db: Session, component: Component) -> ComponentOut:
    result = ComponentOut.model_validate(component)
    result.attributes = _attributes_for(db, "component", component.id)
    return result


def _equipment_out(db: Session, equipment: EquipmentModel) -> EquipmentOut:
    result = EquipmentOut.model_validate(equipment)
    result.attributes = _attributes_for(db, "equipment_model", equipment.id)
    return result


# ---------------------------------------------------------------------------
# Vista completa del catálogo
# ---------------------------------------------------------------------------


@router.get("/tree")
def catalog_tree(db: Session = Depends(get_db)) -> dict:
    categories = db.scalars(select(Category).order_by(Category.sort_order, Category.name)).all()
    equipment_models = db.scalars(
        select(EquipmentModel)
        .options(selectinload(EquipmentModel.components).selectinload(Component.fraction))
        .order_by(EquipmentModel.name)
    ).all()
    loose_components = db.scalars(
        select(Component)
        .where(Component.equipment_model_id.is_(None))
        .options(selectinload(Component.fraction))
        .order_by(Component.name)
    ).all()

    return {
        "categories": [
            {
                "id": category.id,
                "code": category.code,
                "name": category.name,
                "description": category.description,
                "subcategories": [
                    {
                        "id": sub.id,
                        "name": sub.name,
                        "factor_id": sub.factor_id,
                        "description": sub.description,
                    }
                    for sub in category.subcategories
                ],
            }
            for category in categories
        ],
        "brands": [
            {"id": brand.id, "name": brand.name}
            for brand in db.scalars(select(Brand).order_by(Brand.name)).all()
        ],
        "attribute_defs": [
            {
                "id": definition.id,
                "name": definition.name,
                "data_type": definition.data_type,
                "unit": definition.unit,
                "options": json.loads(definition.options_json or "[]"),
                "scope": definition.scope,
                "is_active": definition.is_active,
            }
            for definition in db.scalars(select(AttributeDef).order_by(AttributeDef.name)).all()
        ],
        "fractions": [
            {
                "id": fraction.id,
                "name": fraction.name,
                "type": fraction.type,
                "color": fraction.color,
                "factor_id": fraction.factor_id,
                "active": fraction.active,
            }
            for fraction in db.scalars(select(Fraction).order_by(Fraction.sort_order, Fraction.name)).all()
        ],
        "factors": [
            {
                "id": factor.id,
                "key": factor.key,
                "label": factor.label,
                "mode": factor.mode,
                "unit": factor.unit,
            }
            for factor in db.scalars(select(Factor).order_by(Factor.key)).all()
        ],
        "equipment": [
            {
                "id": equipment.id,
                "name": equipment.name,
                "brand_id": equipment.brand_id,
                "subcategory_id": equipment.subcategory_id,
                "typical_weight_kg": equipment.typical_weight_kg,
                "notes": equipment.notes,
                "attributes": _attributes_for(db, "equipment_model", equipment.id),
                "components": [
                    _component_out(db, component).model_dump() for component in equipment.components
                ],
            }
            for equipment in equipment_models
        ],
        "loose_components": [_component_out(db, component).model_dump() for component in loose_components],
    }


# ---------------------------------------------------------------------------
# Categorías y subcategorías
# ---------------------------------------------------------------------------


@router.post("/categories", response_model=CategoryOut, status_code=status.HTTP_201_CREATED)
def create_category(payload: CategoryIn, db: Session = Depends(get_db)) -> CategoryOut:
    if db.scalar(select(Category).where(Category.code == payload.code)):
        _error(409, f"Ya existe la categoría con código '{payload.code}'.")
    category = Category(**payload.model_dump())
    db.add(category)
    db.commit()
    db.refresh(category)
    return category


@router.put("/categories/{category_id}", response_model=CategoryOut)
def update_category(category_id: int, payload: CategoryIn, db: Session = Depends(get_db)) -> CategoryOut:
    category = _get(db, Category, category_id, "la categoría")
    for attribute, value in payload.model_dump().items():
        setattr(category, attribute, value)
    db.commit()
    db.refresh(category)
    return category


@router.delete("/categories/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_category(category_id: int, db: Session = Depends(get_db)) -> None:
    category = _get(db, Category, category_id, "la categoría")
    if category.subcategories:
        _error(409, "La categoría tiene subcategorías: elimínelas primero.")
    db.delete(category)
    db.commit()


@router.post("/subcategories", response_model=SubcategoryOut, status_code=status.HTTP_201_CREATED)
def create_subcategory(payload: SubcategoryIn, db: Session = Depends(get_db)) -> SubcategoryOut:
    _get(db, Category, payload.category_id, "la categoría")
    if db.scalar(
        select(Subcategory).where(
            Subcategory.category_id == payload.category_id,
            Subcategory.name == payload.name,
        )
    ):
        _error(409, "Ya existe esa subcategoría en la categoría.")
    subcategory = Subcategory(**payload.model_dump())
    db.add(subcategory)
    db.commit()
    db.refresh(subcategory)
    return subcategory


@router.put("/subcategories/{subcategory_id}", response_model=SubcategoryOut)
def update_subcategory(
    subcategory_id: int, payload: SubcategoryIn, db: Session = Depends(get_db)
) -> SubcategoryOut:
    subcategory = _get(db, Subcategory, subcategory_id, "la subcategoría")
    for attribute, value in payload.model_dump().items():
        setattr(subcategory, attribute, value)
    db.commit()
    db.refresh(subcategory)
    return subcategory


@router.delete("/subcategories/{subcategory_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_subcategory(subcategory_id: int, db: Session = Depends(get_db)) -> None:
    subcategory = _get(db, Subcategory, subcategory_id, "la subcategoría")
    if subcategory.equipment_models:
        _error(409, "La subcategoría tiene modelos de equipo: elimínelos primero.")
    db.delete(subcategory)
    db.commit()


# ---------------------------------------------------------------------------
# Marcas
# ---------------------------------------------------------------------------


@router.post("/brands", response_model=BrandOut, status_code=status.HTTP_201_CREATED)
def create_brand(payload: BrandIn, db: Session = Depends(get_db)) -> BrandOut:
    if db.scalar(select(Brand).where(Brand.name == payload.name)):
        _error(409, "Ya existe esa marca.")
    brand = Brand(**payload.model_dump())
    db.add(brand)
    db.commit()
    db.refresh(brand)
    return brand


@router.put("/brands/{brand_id}", response_model=BrandOut)
def update_brand(brand_id: int, payload: BrandIn, db: Session = Depends(get_db)) -> BrandOut:
    brand = _get(db, Brand, brand_id, "la marca")
    brand.name = payload.name
    db.commit()
    db.refresh(brand)
    return brand


@router.delete("/brands/{brand_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_brand(brand_id: int, db: Session = Depends(get_db)) -> None:
    brand = _get(db, Brand, brand_id, "la marca")
    if brand.equipment_models:
        _error(409, "La marca tiene modelos asociados: elimínelos primero.")
    db.delete(brand)
    db.commit()


# ---------------------------------------------------------------------------
# Atributos dinámicos
# ---------------------------------------------------------------------------


@router.post("/attributes", response_model=AttributeDefOut, status_code=status.HTTP_201_CREATED)
def create_attribute(payload: AttributeDefIn, db: Session = Depends(get_db)) -> AttributeDefOut:
    if db.scalar(select(AttributeDef).where(AttributeDef.name == payload.name)):
        _error(409, "Ya existe ese atributo.")
    definition = AttributeDef(
        name=payload.name,
        data_type=payload.data_type,
        unit=payload.unit,
        options_json=json.dumps(payload.options, ensure_ascii=False),
        scope=payload.scope,
        is_active=payload.is_active,
    )
    db.add(definition)
    db.commit()
    db.refresh(definition)
    return definition


@router.put("/attributes/{attribute_id}", response_model=AttributeDefOut)
def update_attribute(
    attribute_id: int, payload: AttributeDefIn, db: Session = Depends(get_db)
) -> AttributeDefOut:
    definition = _get(db, AttributeDef, attribute_id, "el atributo")
    definition.name = payload.name
    definition.data_type = payload.data_type
    definition.unit = payload.unit
    definition.options_json = json.dumps(payload.options, ensure_ascii=False)
    definition.scope = payload.scope
    definition.is_active = payload.is_active
    db.commit()
    db.refresh(definition)
    return definition


@router.delete("/attributes/{attribute_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_attribute(attribute_id: int, db: Session = Depends(get_db)) -> None:
    definition = _get(db, AttributeDef, attribute_id, "el atributo")
    for value in db.scalars(
        select(AttributeValue).where(AttributeValue.definition_id == attribute_id)
    ).all():
        db.delete(value)
    db.flush()
    db.delete(definition)
    db.commit()


# ---------------------------------------------------------------------------
# Fracciones
# ---------------------------------------------------------------------------


@router.post("/fractions", response_model=FractionOut, status_code=status.HTTP_201_CREATED)
def create_fraction(payload: FractionIn, db: Session = Depends(get_db)) -> FractionOut:
    if db.scalar(select(Fraction).where(Fraction.name == payload.name)):
        _error(409, "Ya existe esa fracción.")
    fraction = Fraction(**payload.model_dump())
    db.add(fraction)
    db.commit()
    db.refresh(fraction)
    return fraction


@router.put("/fractions/{fraction_id}", response_model=FractionOut)
def update_fraction(
    fraction_id: int, payload: FractionIn, db: Session = Depends(get_db)
) -> FractionOut:
    fraction = _get(db, Fraction, fraction_id, "la fracción")
    for attribute, value in payload.model_dump().items():
        setattr(fraction, attribute, value)
    db.commit()
    db.refresh(fraction)
    return fraction


@router.delete("/fractions/{fraction_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_fraction(fraction_id: int, db: Session = Depends(get_db)) -> None:
    """Baja lógica: quita la fracción del alta sin borrar su historial.

    Los componentes y escenarios que la referencian siguen funcionando: el motor
    calcula con normalidad y el nombre se conserva en los escenarios guardados.
    """
    fraction = _get(db, Fraction, fraction_id, "la fracción")
    fraction.active = False
    db.commit()


@router.post("/fractions/{fraction_id}/activate", response_model=FractionOut)
def activate_fraction(fraction_id: int, db: Session = Depends(get_db)) -> FractionOut:
    """Reactiva una fracción dada de baja previamente."""
    fraction = _get(db, Fraction, fraction_id, "la fracción")
    fraction.active = True
    db.commit()
    db.refresh(fraction)
    return fraction


# ---------------------------------------------------------------------------
# Modelos de equipo
# ---------------------------------------------------------------------------


@router.post("/equipment", response_model=EquipmentOut, status_code=status.HTTP_201_CREATED)
def create_equipment(payload: EquipmentIn, db: Session = Depends(get_db)) -> EquipmentOut:
    _get(db, Subcategory, payload.subcategory_id, "la subcategoría")
    if payload.brand_id is not None:
        _get(db, Brand, payload.brand_id, "la marca")
    attributes = payload.attributes
    equipment = EquipmentModel(**payload.model_dump(exclude={"attributes"}))
    db.add(equipment)
    db.flush()
    _sync_attributes(db, "equipment_model", equipment.id, attributes)
    db.commit()
    return _equipment_out(db, equipment)


@router.put("/equipment/{equipment_id}", response_model=EquipmentOut)
def update_equipment(
    equipment_id: int, payload: EquipmentIn, db: Session = Depends(get_db)
) -> EquipmentOut:
    equipment = _get(db, EquipmentModel, equipment_id, "el modelo de equipo")
    for attribute, value in payload.model_dump(exclude={"attributes"}).items():
        setattr(equipment, attribute, value)
    _sync_attributes(db, "equipment_model", equipment.id, payload.attributes)
    db.commit()
    return _equipment_out(db, equipment)


@router.delete("/equipment/{equipment_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_equipment(equipment_id: int, db: Session = Depends(get_db)) -> None:
    equipment = _get(db, EquipmentModel, equipment_id, "el modelo de equipo")
    components = db.scalars(
        select(Component).where(Component.equipment_model_id == equipment_id)
    ).all()
    for component in components:
        for component_id in _component_ids(db, component.id):
            _delete_attributes(db, "component", component_id)
    db.flush()
    _delete_attributes(db, "equipment_model", equipment_id)
    db.flush()
    for component in components:
        db.delete(component)
    db.delete(equipment)
    db.commit()


# ---------------------------------------------------------------------------
# Componentes (BOM y sueltos)
# ---------------------------------------------------------------------------


@router.post("/components", response_model=ComponentOut, status_code=status.HTTP_201_CREATED)
def create_component(payload: ComponentIn, db: Session = Depends(get_db)) -> ComponentOut:
    if payload.equipment_model_id is not None:
        _get(db, EquipmentModel, payload.equipment_model_id, "el modelo de equipo")
    if payload.fraction_id is not None:
        _get(db, Fraction, payload.fraction_id, "la fracción")
    if payload.parent_id is not None:
        _get(db, Component, payload.parent_id, "el componente padre")
    attributes = payload.attributes
    component = Component(**payload.model_dump(exclude={"attributes"}))
    db.add(component)
    db.flush()
    _sync_attributes(db, "component", component.id, attributes)
    db.commit()
    return _component_out(db, component)


@router.put("/components/{component_id}", response_model=ComponentOut)
def update_component(
    component_id: int, payload: ComponentIn, db: Session = Depends(get_db)
) -> ComponentOut:
    component = _get(db, Component, component_id, "el componente")
    if payload.parent_id == component_id:
        _error(400, "Un componente no puede ser su propio padre.")
    for attribute, value in payload.model_dump(exclude={"attributes"}).items():
        setattr(component, attribute, value)
    _sync_attributes(db, "component", component.id, payload.attributes)
    db.commit()
    return _component_out(db, component)


@router.delete("/components/{component_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_component(component_id: int, db: Session = Depends(get_db)) -> None:
    component = _get(db, Component, component_id, "el componente")
    for related_id in _component_ids(db, component_id):
        _delete_attributes(db, "component", related_id)
    db.flush()
    db.delete(component)
    db.commit()
