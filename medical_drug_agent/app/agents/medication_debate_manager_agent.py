from __future__ import annotations

from medical_drug_agent.app.agents.base import AgentResult, BaseAgent
from medical_drug_agent.app.debate.debate_manager import MedicationDebateManager
from medical_drug_agent.app.debate.schemas import CandidateDebateOpinion


class MedicationDebateManagerAgent(BaseAgent):
    agent_name = "medication-debate-manager-agent"

    def __init__(self, manager: MedicationDebateManager | None = None) -> None:
        self.manager = manager or MedicationDebateManager()

    def run(self, state: dict) -> AgentResult:
        if bool(state.get("stop_candidate_recommendation")):
            summary, results = self.manager.aggregate({}, red_flag_blocked=True)
            return AgentResult(
                agent_name=self.agent_name,
                status="skipped",
                output={"medication_debate_summary": summary, "debate_results": results},
            )
        if not list(state.get("candidate_safety_results", []) or []):
            summary, results = self.manager.aggregate({}, red_flag_blocked=False)
            return AgentResult(
                agent_name=self.agent_name,
                status="skipped",
                output={"medication_debate_summary": summary, "debate_results": results},
            )
        return super().run(state)

    def _run_impl(self, state: dict) -> dict:
        opinions_by_candidate: dict[str, list[CandidateDebateOpinion]] = {}
        for key in (
            "symptom_fit_opinions",
            "interaction_risk_opinions",
            "patient_factor_opinions",
            "dose_reasoning_opinions",
            "evidence_review_opinions",
        ):
            for candidate_drug, items in dict(state.get(key, {}) or {}).items():
                opinions_by_candidate.setdefault(candidate_drug, []).extend(list(items or []))
        summary, results = self.manager.aggregate(opinions_by_candidate, red_flag_blocked=False)
        return {"medication_debate_summary": summary, "debate_results": results}
