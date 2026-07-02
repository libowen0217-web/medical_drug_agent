from __future__ import annotations

from medical_drug_agent.app.agents.base import BaseAgent
from medical_drug_agent.app.symptom.disease_matcher import DiseaseMatcher, REFERRAL_MESSAGE


class DiseaseCandidateAgent(BaseAgent):
    agent_name = "disease-candidate-agent"

    def __init__(self, matcher: DiseaseMatcher | None = None) -> None:
        self.matcher = matcher or DiseaseMatcher()

    def _run_impl(self, state: dict) -> dict:
        payload = dict(state.get("input_payload", {}) or {})
        result = self.matcher.match(
            symptom_text=str(payload.get("symptom_text", "") or ""),
            parsed_symptoms=list(state.get("parsed_symptoms", []) or []),
        )
        referral_required = bool(result.get("referral_required"))
        return {
            **result,
            "disease_library_used": True,
            "stop_candidate_recommendation": bool(state.get("stop_candidate_recommendation")) or referral_required,
            "disease_referral_message": REFERRAL_MESSAGE if referral_required else "",
        }
