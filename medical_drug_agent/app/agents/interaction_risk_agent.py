from __future__ import annotations

from medical_drug_agent.app.agents.base import AgentResult, BaseAgent
from medical_drug_agent.app.debate.schemas import CandidateDebateOpinion
from medical_drug_agent.app.debate.scoring import DebateScorer


class InteractionRiskAgent(BaseAgent):
    agent_name = "interaction-risk-agent"

    def run(self, state: dict) -> AgentResult:
        if bool(state.get("stop_candidate_recommendation")) or not list(state.get("candidate_safety_results", []) or []):
            return AgentResult(agent_name=self.agent_name, status="skipped", output={"interaction_risk_opinions": {}})
        return super().run(state)

    def _run_impl(self, state: dict) -> dict:
        opinions: dict[str, list[CandidateDebateOpinion]] = {}
        for result in list(state.get("candidate_safety_results", []) or []):
            response = result.safety_response or {}
            data = response.get("data") or {}
            risk_level = str(data.get("overall_risk_level", "unknown") or "unknown").lower()
            score_delta = DebateScorer.interaction_risk_delta(risk_level)
            findings = list(data.get("risk_findings", []) or [])
            evidence_refs = self._extract_evidence_refs(findings)
            if risk_level in {"low", "unknown"}:
                opinion = "在当前本地规则下，未发现明确高风险信号，但不代表不存在风险。"
            else:
                opinion = f"在当前本地规则下检测到 {risk_level} 风险信号，需要进一步复核。"
            opinions.setdefault(result.candidate_drug, []).append(
                CandidateDebateOpinion(
                    candidate_drug=result.candidate_drug,
                    agent_name=self.agent_name,
                    score_delta=score_delta,
                    risk_level=risk_level,
                    opinion=opinion,
                    reasons=[self._risk_reason(risk_level, findings)],
                    evidence_refs=evidence_refs,
                )
            )
        return {"interaction_risk_opinions": opinions}

    @staticmethod
    def _risk_reason(risk_level: str, findings: list[dict]) -> str:
        if findings:
            first_title = str(findings[0].get("title", "") or "").strip()
            if first_title:
                return f"候选药安全检查返回 {risk_level} 风险级别，主要信号涉及：{first_title}。"
        if risk_level in {"low", "unknown"}:
            return "候选药安全检查未返回明确高风险信号，仍需结合个体情况继续确认。"
        return f"候选药安全检查返回 {risk_level} 风险级别。"

    @staticmethod
    def _extract_evidence_refs(findings: list[dict]) -> list[str]:
        refs: list[str] = []
        for finding in findings:
            for item in list(finding.get("evidence_items", []) or []):
                label = str(item.get("citation_label") or item.get("source_name") or item.get("evidence_id") or "").strip()
                if label and label not in refs:
                    refs.append(label)
        return refs
