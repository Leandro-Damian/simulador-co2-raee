from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field

ModeIn = Literal["reuse", "recycling", "no_recovery"]
KindIn = Literal["equipment", "component", "fraction"]


class CalculateItemIn(BaseModel):
    kind: KindIn
    id: int = Field(gt=0)
    quantity: int = Field(default=1, gt=0)
    weight_kg: float | None = Field(default=None, ge=0)
    mode: ModeIn
    attributes: dict[str, Any] | None = None


class CalculateRequest(BaseModel):
    items: list[CalculateItemIn] = Field(default_factory=list)
    scenario_id: int | None = Field(default=None, gt=0)


class BreakdownLine(BaseModel):
    label: str
    factor_key: str
    weight_kg: float
    factor_value: float
    co2_kg: float


class CalculationLine(BaseModel):
    label: str
    kind: KindIn
    mode: ModeIn
    mode_label: str
    quantity: int
    weight_kg: float
    factor_key: str
    factor_value: float
    factor_unit: str
    co2_kg: float
    excluded_reason: str | None = None
    breakdown: list[BreakdownLine] | None = None


class CalculationTotals(BaseModel):
    total_weight_kg: float
    co2_reuse: float
    co2_recycling: float
    co2_no_recovery: float
    co2_total: float


class EquivalenceResult(BaseModel):
    label: str
    value: float
    display: str
    unit: str
    note: str | None = None


class CalculationResult(BaseModel):
    lines: list[CalculationLine]
    totals: CalculationTotals
    equivalences: list[EquivalenceResult]
    warnings: list[str]
