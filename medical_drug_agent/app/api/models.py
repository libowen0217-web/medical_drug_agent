from __future__ import annotations

from pydantic import BaseModel, Field


class DrugSafetyAPIRequest(BaseModel):
    current_drugs: list[str] = Field(default_factory=list)
    new_drug: str
    age: int | None = None
    diseases: list[str] = Field(default_factory=list)
    patient_factors: list[str] = Field(default_factory=list)
    dose: dict | None = None

