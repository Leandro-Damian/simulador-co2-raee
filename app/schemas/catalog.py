from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field, field_validator

DATA_TYPES = ("text", "number", "select")
SCOPES = ("equipment", "component")
FRACTION_TYPES = ("metal", "plastic", "other")


class CategoryIn(BaseModel):
    code: str = Field(min_length=1, max_length=40, pattern=r"^[A-Z0-9_]+$")
    name: str = Field(min_length=1, max_length=120)
    description: str | None = None
    sort_order: int = 0


class SubcategoryIn(BaseModel):
    category_id: int
    name: str = Field(min_length=1, max_length=140)
    description: str | None = None
    factor_id: int | None = None
    sort_order: int = 0


class BrandIn(BaseModel):
    name: str = Field(min_length=1, max_length=120)


class AttributeDefIn(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    data_type: str = "text"
    unit: str | None = None
    options: list[str] = Field(default_factory=list)
    scope: str = "component"
    is_active: bool = True

    @field_validator("data_type")
    @classmethod
    def check_type(cls, value: str) -> str:
        if value not in DATA_TYPES:
            raise ValueError(f"Tipo inválido: {value}")
        return value

    @field_validator("scope")
    @classmethod
    def check_scope(cls, value: str) -> str:
        if value not in SCOPES:
            raise ValueError(f"Scope inválido: {value}")
        return value


class EquipmentIn(BaseModel):
    subcategory_id: int
    brand_id: int | None = None
    name: str = Field(min_length=1, max_length=160)
    typical_weight_kg: float = Field(default=0.0, ge=0)
    notes: str | None = None
    attributes: dict[str, str] = Field(default_factory=dict)


class ComponentIn(BaseModel):
    name: str = Field(min_length=1, max_length=160)
    equipment_model_id: int | None = None
    parent_id: int | None = None
    fraction_id: int | None = None
    weight_kg: float = Field(default=0.0, ge=0)
    quantity: int = Field(default=1, ge=1)
    notes: str | None = None
    attributes: dict[str, str] = Field(default_factory=dict)


class FractionIn(BaseModel):
    name: str = Field(min_length=1, max_length=80)
    type: str = "other"
    color: str | None = None
    factor_id: int | None = None
    sort_order: int = 0
    active: bool = True

    @field_validator("type")
    @classmethod
    def check_type(cls, value: str) -> str:
        if value not in FRACTION_TYPES:
            raise ValueError(f"Tipo de fracción inválido: {value}")
        return value


class CategoryOut(CategoryIn):
    id: int
    model_config = ConfigDict(from_attributes=True)


class SubcategoryOut(SubcategoryIn):
    id: int
    model_config = ConfigDict(from_attributes=True)


class BrandOut(BrandIn):
    id: int
    model_config = ConfigDict(from_attributes=True)


class AttributeDefOut(AttributeDefIn):
    id: int
    model_config = ConfigDict(from_attributes=True)


class FractionOut(FractionIn):
    id: int
    model_config = ConfigDict(from_attributes=True)


class EquipmentOut(EquipmentIn):
    id: int
    model_config = ConfigDict(from_attributes=True)


class ComponentOut(ComponentIn):
    id: int
    model_config = ConfigDict(from_attributes=True)
