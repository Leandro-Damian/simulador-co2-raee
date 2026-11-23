from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field, field_validator

VALID_MODES = ("reuse", "recycling", "no_recovery", "material", "equivalence", "all")


def _validate_mode(value: str) -> str:
    if value not in VALID_MODES:
        raise ValueError(f"Modo inválido: {value}. Use uno de {', '.join(VALID_MODES)}")
    return value


class FactorBase(BaseModel):
    label: str = Field(min_length=1, max_length=180)
    value: float
    unit: str = Field(min_length=1, max_length=40)
    mode: str
    source: str | None = None
    note: str | None = None
    active: bool = True

    @field_validator("mode")
    @classmethod
    def check_mode(cls, value: str) -> str:
        return _validate_mode(value)


class FactorCreate(FactorBase):
    key: str = Field(min_length=1, max_length=80, pattern=r"^[a-z0-9_]+$")


class FactorUpdate(BaseModel):
    label: str | None = Field(default=None, min_length=1, max_length=180)
    value: float | None = None
    unit: str | None = Field(default=None, min_length=1, max_length=40)
    mode: str | None = None
    source: str | None = None
    note: str | None = None
    active: bool | None = None

    @field_validator("mode")
    @classmethod
    def check_mode(cls, value: str | None) -> str | None:
        return _validate_mode(value) if value is not None else None


class FactorOut(FactorBase):
    id: int
    key: str

    model_config = ConfigDict(from_attributes=True)


class EquivalenceUpdate(BaseModel):
    label: str | None = Field(default=None, min_length=1, max_length=180)
    value: float | None = None
    unit: str | None = Field(default=None, min_length=1, max_length=80)
    note: str | None = None
    active: bool | None = None


class EquivalenceOut(BaseModel):
    id: int
    label: str
    value: float
    unit: str
    note: str | None = None
    active: bool

    model_config = ConfigDict(from_attributes=True)
