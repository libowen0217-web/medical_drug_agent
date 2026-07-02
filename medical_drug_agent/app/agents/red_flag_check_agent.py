from __future__ import annotations

from medical_drug_agent.app.agents.base import BaseAgent
from medical_drug_agent.app.symptom.red_flag_checker import RedFlagChecker


class RedFlagCheckAgent(BaseAgent):
    agent_name = "red-flag-check-agent"

    def __init__(self, checker: RedFlagChecker | None = None) -> None:
        self.checker = checker or RedFlagChecker()

    def _run_impl(self, state: dict) -> dict:
        payload = dict(state.get("input_payload", {}) or {})
        red_flags = self.checker.check(
            symptom_text=str(payload.get("symptom_text", "") or ""),
            age=payload.get("age"),
            temperature_c=payload.get("temperature_c"),
            duration_days=payload.get("duration_days"),
            patient_factors=list(payload.get("patient_factors", []) or []),
        )
        return {
            "red_flags": red_flags,
            "stop_candidate_recommendation": bool(red_flags),
        }

