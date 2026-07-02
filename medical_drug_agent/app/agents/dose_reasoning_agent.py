from __future__ import annotations

from medical_drug_agent.app.agents.base import AgentResult, BaseAgent
from medical_drug_agent.app.debate.schemas import CandidateDebateOpinion
from medical_drug_agent.app.debate.scoring import DebateScorer


class DoseReasoningAgent(BaseAgent):
    agent_name = "dose-reasoning-agent"

    def run(self, state: dict) -> AgentResult:
        if bool(state.get("stop_candidate_recommendation")) or not list(state.get("candidate_safety_results", []) or []):
            return AgentResult(agent_name=self.agent_name, status="skipped", output={"dose_reasoning_opinions": {}})
        return super().run(state)

    def _run_impl(self, state: dict) -> dict:
        opinions: dict[str, list[CandidateDebateOpinion]] = {}
        for result in list(state.get("candidate_safety_results", []) or []):
            response = result.safety_response or {}
            data = response.get("data") or {}
            findings = list(data.get("risk_findings", []) or [])
            dose_results = list(data.get("dose_results", []) or [])
            dose_level, reason, refs = self._infer_dose_level(dose_results, findings)
            opinions.setdefault(result.candidate_drug, []).append(
                CandidateDebateOpinion(
                    candidate_drug=result.candidate_drug,
                    agent_name=self.agent_name,
                    score_delta=DebateScorer.dose_delta(dose_level),
                    risk_level="unknown" if dose_level == "missing" else dose_level,
                    opinion="剂量信息复核完成。",
                    reasons=[reason],
                    evidence_refs=refs,
                )
            )
        return {"dose_reasoning_opinions": opinions}

    @staticmethod
    def _infer_dose_level(dose_results: list[dict], findings: list[dict]) -> tuple[str, str, list[str]]:
        refs: list[str] = []
        dose_result = dose_results[0] if dose_results else {}
        dose_source = str(dose_result.get("dose_source", "") or "").lower()
        dose_status = str(dose_result.get("status", "") or "").lower()
        dose_message = str(dose_result.get("message", "") or "").strip()

        if dose_source == "label_reference":
            return (
                "low",
                dose_message or "本次基于说明书参考剂量进行了模拟评估，不代表患者实际用药剂量。",
                refs,
            )

        if dose_source == "missing":
            return (
                "missing",
                dose_message or "当前未提供实际剂量，因此无法完成完整剂量合理性判断。",
                refs,
            )

        max_level = "low"
        reason = dose_message or "已提供剂量信息，当前未从本地规则中识别出更高等级的剂量风险信号。"
        level_order = {"low": 0, "medium": 1, "high": 2}
        for finding in findings:
            if str(finding.get("source", "")).lower() != "dose":
                continue
            level = str(finding.get("risk_level", "medium") or "medium").lower()
            if level_order.get(level, 0) >= level_order.get(max_level, 0):
                max_level = level
                reason = str(finding.get("description", "") or "").strip() or reason
            for item in list(finding.get("evidence_items", []) or []):
                label = str(item.get("citation_label") or item.get("source_name") or item.get("evidence_id") or "").strip()
                if label and label not in refs:
                    refs.append(label)

        if dose_status == "missing_dose":
            return "missing", reason, refs
        return max_level, reason, refs
