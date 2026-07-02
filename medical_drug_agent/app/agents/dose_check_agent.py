from __future__ import annotations

from medical_drug_agent.app.agents.base import BaseAgent
from medical_drug_agent.app.dose.checker import DoseChecker
from medical_drug_agent.app.schemas import DoseInput


class DoseCheckAgent(BaseAgent):
    agent_name = "dose-check-agent"

    def __init__(self, dose_checker: DoseChecker | None = None) -> None:
        self.dose_checker = dose_checker or DoseChecker()

    def _run_impl(self, state: dict) -> dict:
        payload = dict(state.get("input_payload", {}) or {})
        new_drug = state.get("normalized_new_drug")
        drug_name = new_drug.en_name if new_drug is not None else str(payload.get("new_drug", "") or "")
        dose_payload = payload.get("dose")
        dose_mode = None if not isinstance(dose_payload, dict) else str(dose_payload.get("dose_mode", "") or "").strip()
        dose_input = DoseInput(
            drug_name=drug_name,
            single_dose_mg=None if not dose_payload else dose_payload.get("single_dose_mg"),
            times_per_day=None if not dose_payload else dose_payload.get("times_per_day"),
            duration_days=None if not dose_payload else dose_payload.get("duration_days"),
            dose_mode=dose_mode or None,
            allow_reference_dose=dose_mode == "label_reference",
            dose_context="drug_safety_otc" if dose_mode == "label_reference" else "drug_safety",
        )
        return {"dose_results": [self.dose_checker.check(dose_input)]}
