from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

ModeIn = Literal["reuse", "recycling", "no_recovery"]
KindIn = Literal["equipment", "component", "fraction"]


class ScenarioItemPayload(BaseModel):
    id: int | None = None
    kind: KindIn
    entity_id: int = Field(gt=0)
    quantity: int = Field(default=1, gt=0)
    weight_kg: float | None = Field(default=None, ge=0)
    mode: ModeIn | None = None
    attributes: dict[str, Any] = Field(default_factory=dict)


class ScenarioPayload(BaseModel):
    name: str = Field(min_length=1, max_length=180)
    default_mode: ModeIn = "reuse"
    notes: str | None = None
    items: list[ScenarioItemPayload] = Field(default_factory=list)


class ScenarioItemOut(BaseModel):
    id: int
    kind: KindIn
    entity_id: int
    entity_label: str
    quantity: int
    weight_kg: float
    mode: str | None
    attributes: dict[str, Any]


class ScenarioOut(BaseModel):
    id: int
    name: str
    created_at: datetime
    default_mode: str
    notes: str | None
    items: list[ScenarioItemOut]
    total_co2_kg: float = 0.0

    model_config = ConfigDict(from_attributes=True)
