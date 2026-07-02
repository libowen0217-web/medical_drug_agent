from __future__ import annotations

from medical_drug_agent.app.agents.base import AgentResult, BaseAgent
from medical_drug_agent.app.agents.supervisor_agent import SupervisorAgent
from medical_drug_agent.app.api_contract import build_error_response, build_success_response
from medical_drug_agent.app.dose.checker import DoseChecker
from medical_drug_agent.app.schemas import DoseInput
from medical_drug_agent.app.serialization import to_dict
from medical_drug_agent.app.symptom.schemas import CandidateSafetyResult


class CandidateSafetyAgent(BaseAgent):
    agent_name = "candidate-safety-agent"
    ENGINE_VERSION = "local-csv-mvp-v1"

    def __init__(self, supervisor_factory=None, dose_checker: DoseChecker | None = None) -> None:
        self.supervisor_factory = supervisor_factory or (lambda: SupervisorAgent(enable_audit=False, enable_llm=False))
        self.dose_checker = dose_checker or DoseChecker()

    def run(self, state: dict) -> AgentResult:
        if bool(state.get("stop_candidate_recommendation")):
            return AgentResult(
                agent_name=self.agent_name,
                status="skipped",
                output={"candidate_safety_results": []},
            )
        return super().run(state)

    def _run_impl(self, state: dict) -> dict:
        payload = dict(state.get("input_payload", {}) or {})
        current_drugs = list(payload.get("current_drugs", []) or [])

        results: list[CandidateSafetyResult] = []
        for candidate in list(state.get("otc_candidates", []) or []):
            for candidate_drug in list(getattr(candidate, "candidate_drugs", []) or []):
                try:
                    if current_drugs:
                        dose_payload = self._build_candidate_dose_payload(payload.get("dose"))
                        response = self.supervisor_factory().run(
                            {
                                "current_drugs": current_drugs,
                                "new_drug": candidate_drug,
                                "age": payload.get("age"),
                                "diseases": list(payload.get("diseases", []) or []),
                                "patient_factors": list(payload.get("patient_factors", []) or []),
                                "dose": dose_payload,
                            }
                        )
                    else:
                        response = self._build_context_only_response(candidate_drug, candidate, payload)
                except Exception as exc:
                    response = build_error_response(
                        error_code="WORKFLOW_ERROR",
                        message=f"候选药安全检查失败：{exc}",
                        metadata={"engine_version": self.ENGINE_VERSION},
                    )
                results.append(CandidateSafetyResult(candidate_drug=candidate_drug, safety_response=response))
        return {"candidate_safety_results": results}

    @staticmethod
    def _build_candidate_dose_payload(dose_payload: object) -> dict:
        payload = dict(dose_payload or {}) if isinstance(dose_payload, dict) else {}
        if not payload:
            return {"dose_mode": "label_reference"}
        if not str(payload.get("dose_mode", "") or "").strip():
            payload["dose_mode"] = "label_reference"
        return payload

    def _build_context_only_response(self, candidate_drug: str, candidate: object, payload: dict) -> dict:
        findings: list[dict] = []
        diseases = list(payload.get("diseases", []) or [])
        patient_factors = list(payload.get("patient_factors", []) or [])
        allergies = list(payload.get("allergies", []) or [])
        caution = str(getattr(candidate, "caution", "") or "").strip()

        if caution:
            findings.append(
                {
                    "source": "candidate_context",
                    "risk_level": "medium",
                    "title": "基础疾病或特殊人群注意事项",
                    "description": caution,
                    "mechanism": "基于当前症状规则、基础疾病、特殊人群或过敏史生成的候选药注意事项。",
                    "recommendation": "请由医生或药师结合患者实际情况进一步复核。",
                    "related_drugs": [candidate_drug],
                    "related_diseases": diseases,
                    "evidence_items": [],
                }
            )

        allergy_hits = [item for item in allergies if item and (item in candidate_drug or candidate_drug in item)]
        if allergy_hits:
            findings.append(
                {
                    "source": "allergy",
                    "risk_level": "high",
                    "title": "疑似过敏风险",
                    "description": f"过敏史中包含与 {candidate_drug} 相关的条目：{'；'.join(allergy_hits)}。",
                    "mechanism": "候选药与手动录入的过敏史存在直接名称命中。",
                    "recommendation": "未进一步核实前，不宜优先考虑该候选药。",
                    "related_drugs": [candidate_drug],
                    "related_diseases": [],
                    "evidence_items": [],
                }
            )

        candidate_dose_payload = self._build_candidate_dose_payload(payload.get("dose"))
        dose_result = self.dose_checker.check(
            DoseInput(
                drug_name=candidate_drug,
                single_dose_mg=candidate_dose_payload.get("single_dose_mg"),
                times_per_day=candidate_dose_payload.get("times_per_day"),
                duration_days=candidate_dose_payload.get("duration_days"),
                dose_mode=str(candidate_dose_payload.get("dose_mode", "") or "").strip() or None,
                allow_reference_dose=str(candidate_dose_payload.get("dose_mode", "") or "").strip() == "label_reference",
                dose_context="otc_candidate",
            )
        )

        if dose_result.status != "within_reference":
            findings.append(
                {
                    "source": "dose",
                    "risk_level": dose_result.risk_level,
                    "title": "剂量信息提示" if dose_result.status == "missing_dose" else "剂量风险提示",
                    "description": dose_result.message,
                    "mechanism": "基于本地剂量参考进行的候选药剂量安全筛查。",
                    "recommendation": (
                        "建议补充剂量信息后再做完整复核。"
                        if dose_result.status == "missing_dose"
                        else "请结合药品说明书和专业人员意见进一步确认。"
                    ),
                    "related_drugs": [candidate_drug],
                    "related_diseases": [],
                    "evidence_items": [],
                }
            )

        if not findings:
            findings.append(
                {
                    "source": "candidate_context",
                    "risk_level": "low",
                    "title": "未发现额外高风险提示",
                    "description": (
                        "未提供当前用药，因此未进行药物-药物相互作用检查；"
                        "已结合症状、基础疾病、特殊人群和已提供信息完成初步评估。"
                    ),
                    "mechanism": "本次结果仅基于非相互作用维度的本地规则进行筛查。",
                    "recommendation": "最终是否适合使用，仍需由医生或药师结合患者实际情况确认。",
                    "related_drugs": [candidate_drug],
                    "related_diseases": diseases,
                    "evidence_items": [],
                }
            )

        overall_risk_level = self._pick_overall_risk(findings)
        safety_warnings: list[str] = []
        if not payload.get("current_drugs"):
            safety_warnings.append(
                "未提供当前用药，因此未发现药物-药物相互作用项；仍需结合疾病、过敏史、特殊人群和剂量信息评估。"
            )
        if patient_factors:
            safety_warnings.append(f"当前患者因素：{'、'.join(patient_factors)}，请结合个体情况复核。")

        dose_note = dose_result.message
        report_text = (
            f"候选药 {candidate_drug} 已完成初步安全筛查。"
            "本次未提供当前用药，因此未进行药物-药物相互作用检查；"
            "系统仍结合基础疾病、特殊人群、过敏史和剂量信息给出辅助提示。"
            f" 剂量评估说明：{dose_note}"
        )

        return build_success_response(
            data={
                "overall_risk_level": overall_risk_level,
                "normalized_current_drugs": [],
                "normalized_new_drug": None,
                "risk_findings": findings,
                "dose_results": [to_dict(dose_result)],
                "pharmacist_report": report_text,
                "patient_report": report_text,
                "safety_warnings": safety_warnings,
            },
            metadata={
                "engine_version": self.ENGINE_VERSION,
                "current_drug_count": 0,
                "disease_count": len(diseases),
                "risk_finding_count": len(findings),
                "safety_warning_count": len(safety_warnings),
                "has_dose_input": payload.get("dose") is not None,
                "knowledge_backend": "csv",
                "active_knowledge_backend": "csv",
                "fallback_used": False,
                "candidate_context_only": True,
            },
            message="候选药安全检查完成",
        )

    @staticmethod
    def _pick_overall_risk(findings: list[dict]) -> str:
        order = {"high": 3, "medium": 2, "unknown": 1, "low": 0}
        best = "low"
        for item in findings:
            level = str(item.get("risk_level", "low") or "low").lower()
            if order.get(level, 0) > order.get(best, 0):
                best = level
        return best
