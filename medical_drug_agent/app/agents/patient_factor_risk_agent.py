from __future__ import annotations

from medical_drug_agent.app.agents.base import AgentResult, BaseAgent
from medical_drug_agent.app.debate.schemas import CandidateDebateOpinion
from medical_drug_agent.app.debate.scoring import DebateScorer


class PatientFactorRiskAgent(BaseAgent):
    agent_name = "patient-factor-risk-agent"

    def run(self, state: dict) -> AgentResult:
        if bool(state.get("stop_candidate_recommendation")) or not list(state.get("candidate_safety_results", []) or []):
            return AgentResult(agent_name=self.agent_name, status="skipped", output={"patient_factor_opinions": {}})
        return super().run(state)

    def _run_impl(self, state: dict) -> dict:
        payload = dict(state.get("input_payload", {}) or {})
        opinions: dict[str, list[CandidateDebateOpinion]] = {}
        for result in list(state.get("candidate_safety_results", []) or []):
            delta, reasons, cautions = DebateScorer.patient_factor_delta(
                candidate_drug=result.candidate_drug,
                age=payload.get("age"),
                diseases=list(payload.get("diseases", []) or []),
                patient_factors=list(payload.get("patient_factors", []) or []),
            )
            combined_reasons = reasons or ["当前已知年龄、疾病和个体因素下，未额外发现更高等级的个体风险扣分信号。"]
            combined_reasons.extend(item for item in cautions if item not in combined_reasons)
            risk_level = "low"
            if delta <= -20:
                risk_level = "high"
            elif delta < 0:
                risk_level = "medium"
            opinions.setdefault(result.candidate_drug, []).append(
                CandidateDebateOpinion(
                    candidate_drug=result.candidate_drug,
                    agent_name=self.agent_name,
                    score_delta=delta,
                    risk_level=risk_level,
                    opinion="患者因素复核完成。",
                    reasons=combined_reasons,
                    evidence_refs=[],
                )
            )
        return {"patient_factor_opinions": opinions}
