from __future__ import annotations

from medical_drug_agent.app.agents.base import BaseAgent
from medical_drug_agent.app.normalization.mapper import DrugNameMapper
from medical_drug_agent.app.schemas import PatientInfo


class DrugNormalizationAgent(BaseAgent):
    agent_name = "drug-normalization-agent"

    def __init__(self, mapper: DrugNameMapper | None = None) -> None:
        self.mapper = mapper or DrugNameMapper()

    def _run_impl(self, state: dict) -> dict:
        payload = dict(state.get("input_payload", {}) or {})
        current_drugs = list(payload.get("current_drugs", []) or [])
        new_drug = str(payload.get("new_drug", "") or "")
        patient_info = PatientInfo(
            age=payload.get("age"),
            diseases=list(payload.get("diseases", []) or []),
            patient_factors=list(payload.get("patient_factors", []) or []),
        )
        return {
            "normalized_current_drugs": self.mapper.normalize_many(current_drugs),
            "normalized_new_drug": self.mapper.normalize(new_drug),
            "patient_info": patient_info,
        }
