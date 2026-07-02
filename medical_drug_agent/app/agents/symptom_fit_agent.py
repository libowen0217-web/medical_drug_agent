from __future__ import annotations

from medical_drug_agent.app.agents.base import AgentResult, BaseAgent
from medical_drug_agent.app.debate.schemas import CandidateDebateOpinion


class SymptomFitAgent(BaseAgent):
    agent_name = "symptom-fit-agent"

    def run(self, state: dict) -> AgentResult:
        if bool(state.get("stop_candidate_recommendation")) or not list(state.get("otc_candidates", []) or []):
            return AgentResult(agent_name=self.agent_name, status="skipped", output={"symptom_fit_opinions": {}})
        return super().run(state)

    def _run_impl(self, state: dict) -> dict:
        parsed_names = {str(item.symptom_name or "").strip() for item in list(state.get("parsed_symptoms", []) or [])}
        text = " ".join(parsed_names).lower()
        opinions: dict[str, list[CandidateDebateOpinion]] = {}
        for candidate in list(state.get("otc_candidates", []) or []):
            match_level = "insufficient"
            reason = "当前症状与该候选药的匹配信息不足。"
            symptom_group = str(candidate.symptom_group or "").strip()
            if symptom_group and symptom_group.lower() in text:
                match_level = "high"
                reason = f"当前解析出的症状与 {candidate.drug_class} 对应症状组匹配度较高。"
            elif parsed_names:
                match_level = "medium"
                reason = f"当前解析出的症状与 {candidate.drug_class} 存在部分匹配。"
            score_delta = 20 if match_level == "high" else 10 if match_level == "medium" else 0
            for drug in list(candidate.candidate_drugs or []):
                opinions.setdefault(drug, []).append(
                    CandidateDebateOpinion(
                        candidate_drug=drug,
                        agent_name=self.agent_name,
                        score_delta=score_delta,
                        risk_level="low" if score_delta > 0 else "unknown",
                        opinion=f"症状匹配度：{match_level}",
                        reasons=[reason],
                        evidence_refs=[symptom_group] if symptom_group else [],
                    )
                )
        return {"symptom_fit_opinions": opinions}
