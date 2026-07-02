from __future__ import annotations

from medical_drug_agent.app.agents.base import AgentResult, BaseAgent
from medical_drug_agent.app.debate.schemas import CandidateDebateOpinion


class EvidenceReviewAgent(BaseAgent):
    agent_name = "evidence-review-agent"

    def run(self, state: dict) -> AgentResult:
        if bool(state.get("stop_candidate_recommendation")) or not list(state.get("candidate_safety_results", []) or []):
            return AgentResult(agent_name=self.agent_name, status="skipped", output={"evidence_review_opinions": {}})
        return super().run(state)

    def _run_impl(self, state: dict) -> dict:
        opinions: dict[str, list[CandidateDebateOpinion]] = {}
        for result in list(state.get("candidate_safety_results", []) or []):
            response = result.safety_response or {}
            data = response.get("data") or {}
            findings = list(data.get("risk_findings", []) or [])
            refs = self._extract_refs(findings)
            reason = "本地证据摘要可为当前风险提示提供辅助支持，但不等同于正式指南。"
            if not refs:
                reason = "当前未抽取到明确证据引用，结论更多依赖本地规则匹配。"
            opinions.setdefault(result.candidate_drug, []).append(
                CandidateDebateOpinion(
                    candidate_drug=result.candidate_drug,
                    agent_name=self.agent_name,
                    score_delta=0,
                    risk_level="low" if refs else "unknown",
                    opinion="证据复核完成。",
                    reasons=[reason],
                    evidence_refs=refs,
                )
            )
        return {"evidence_review_opinions": opinions}

    @staticmethod
    def _extract_refs(findings: list[dict]) -> list[str]:
        refs: list[str] = []
        for finding in findings:
            for item in list(finding.get("evidence_items", []) or []):
                label = str(item.get("citation_label") or item.get("source_name") or item.get("evidence_id") or "").strip()
                if label and label not in refs:
                    refs.append(label)
        return refs
