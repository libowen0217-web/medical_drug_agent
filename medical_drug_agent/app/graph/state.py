from __future__ import annotations

from typing import Any, TypedDict


class DrugSafetyGraphState(TypedDict, total=False):
    input_payload: dict[str, Any]
    current_drug_inputs: list[str]
    new_drug_input: str
    age: int | None
    diseases: list[str]
    patient_factors: list[str]
    dose: dict[str, Any] | None

    normalized_current_drugs: list[Any]
    normalized_new_drug: Any
    patient_info: Any

    kg_pair_relations: list[Any]
    kg_query_summary: dict[str, Any]

    rule_matches: list[Any]
    dose_results: list[Any]

    risk_summary: Any
    evidence_items: list[Any]
    pharmacist_report: str
    patient_report: str
    safety_warnings: list[str]

    response: dict[str, Any]
    error: dict[str, Any] | None
