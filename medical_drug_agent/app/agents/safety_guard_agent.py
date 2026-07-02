from __future__ import annotations

from medical_drug_agent.app.agents.base import BaseAgent
from medical_drug_agent.app.reporting.safety_filter import SafetyFilter


class SafetyGuardAgent(BaseAgent):
    agent_name = "safety-guard-agent"

    def __init__(self, safety_filter: SafetyFilter | None = None) -> None:
        self.safety_filter = safety_filter or SafetyFilter()

    def _run_impl(self, state: dict) -> dict:
        pharmacist_report, warnings_a = self.safety_filter.validate_and_fix(
            str(state.get("pharmacist_report", "") or "")
        )
        patient_report, warnings_b = self.safety_filter.validate_and_fix(
            str(state.get("patient_report", "") or "")
        )
        return {
            "pharmacist_report": pharmacist_report,
            "patient_report": patient_report,
            "safety_warnings": list(warnings_a) + list(warnings_b),
        }
