from __future__ import annotations

from medical_drug_agent.app.agents.base import BaseAgent
from medical_drug_agent.app.symptom.symptom_parser import SymptomParser


class SymptomIntakeAgent(BaseAgent):
    agent_name = "symptom-intake-agent"

    def __init__(self, parser: SymptomParser | None = None) -> None:
        self.parser = parser or SymptomParser()

    def _run_impl(self, state: dict) -> dict:
        payload = dict(state.get("input_payload", {}) or {})
        symptom_text = str(payload.get("symptom_text", "") or "")
        return {
            "parsed_symptoms": self.parser.parse(symptom_text),
            "symptom_context": {
                "symptom_text": symptom_text,
                "age": payload.get("age"),
                "sex": payload.get("sex"),
                "temperature_c": payload.get("temperature_c"),
                "duration_days": payload.get("duration_days"),
            },
        }

