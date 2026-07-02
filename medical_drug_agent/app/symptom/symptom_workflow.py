from __future__ import annotations

from medical_drug_agent.app.agents.candidate_safety_agent import CandidateSafetyAgent
from medical_drug_agent.app.agents.disease_candidate_agent import DiseaseCandidateAgent
from medical_drug_agent.app.agents.dose_reasoning_agent import DoseReasoningAgent
from medical_drug_agent.app.agents.evidence_review_agent import EvidenceReviewAgent
from medical_drug_agent.app.agents.interaction_risk_agent import InteractionRiskAgent
from medical_drug_agent.app.agents.medication_debate_manager_agent import MedicationDebateManagerAgent
from medical_drug_agent.app.agents.otc_candidate_agent import OTCCandidateAgent
from medical_drug_agent.app.agents.patient_factor_risk_agent import PatientFactorRiskAgent
from medical_drug_agent.app.agents.red_flag_check_agent import RedFlagCheckAgent
from medical_drug_agent.app.agents.safety_guard_agent import SafetyGuardAgent
from medical_drug_agent.app.agents.symptom_consult_report_agent import SymptomConsultReportAgent
from medical_drug_agent.app.agents.symptom_fit_agent import SymptomFitAgent
from medical_drug_agent.app.agents.symptom_intake_agent import SymptomIntakeAgent
from medical_drug_agent.app.api_contract import build_error_response, build_success_response
from medical_drug_agent.app.serialization import to_dict


class SymptomConsultWorkflow:
    ENGINE_VERSION = "local-csv-mvp-v1"

    def __init__(self, enable_audit: bool = False, enable_llm: bool = False) -> None:
        self.enable_audit = enable_audit
        self.enable_llm = enable_llm
        self.agents = [
            SymptomIntakeAgent(),
            RedFlagCheckAgent(),
            DiseaseCandidateAgent(),
            OTCCandidateAgent(),
            CandidateSafetyAgent(),
            SymptomFitAgent(),
            InteractionRiskAgent(),
            PatientFactorRiskAgent(),
            DoseReasoningAgent(),
            EvidenceReviewAgent(),
            MedicationDebateManagerAgent(),
            SymptomConsultReportAgent(),
        ]
        self.safety_guard_agent = SafetyGuardAgent()
        self.debate_agents = {
            "symptom-fit-agent",
            "interaction-risk-agent",
            "patient-factor-risk-agent",
            "dose-reasoning-agent",
            "evidence-review-agent",
            "medication-debate-manager-agent",
        }

    def run(self, payload: dict) -> dict:
        symptom_text = str(payload.get("symptom_text", "") or "").strip()
        if not symptom_text:
            return build_error_response(
                error_code="INVALID_INPUT",
                message="symptom_text 不能为空",
                metadata={"engine_version": self.ENGINE_VERSION, "workflow_type": "symptom_consult"},
            )

        state = {"input_payload": self._sanitize_payload(payload)}
        executed: list[str] = []
        failed: list[str] = []

        for agent in self.agents:
            result = agent.run(state)
            if result.status != "skipped":
                executed.append(result.agent_name)
            if result.output:
                state.update(result.output)
            if result.status == "error":
                failed.append(result.agent_name)
                return build_error_response(
                    error_code=str(result.metadata.get("error_code", "WORKFLOW_ERROR")),
                    message=result.error or f"{agent.agent_name} 执行失败",
                    metadata={
                        "engine_version": self.ENGINE_VERSION,
                        "workflow_type": "symptom_consult",
                        "symptom_agents_executed": executed,
                        "symptom_agents_failed": failed,
                        "red_flag_triggered": bool(state.get("red_flags")),
                    },
                )

        safety_result = self.safety_guard_agent.run(
            {
                "pharmacist_report": str(state.get("consult_report", "") or ""),
                "patient_report": str(state.get("consult_report", "") or ""),
            }
        )
        if safety_result.status == "success":
            state["consult_report"] = str((safety_result.output or {}).get("patient_report", "") or "")
            state["safety_warnings"] = list((safety_result.output or {}).get("safety_warnings", []) or [])

        red_flag_triggered = bool(state.get("red_flags"))
        data = {
            "parsed_symptoms": [to_dict(item) for item in list(state.get("parsed_symptoms", []) or [])],
            "red_flags": [to_dict(item) for item in list(state.get("red_flags", []) or [])],
            "disease_candidates": [to_dict(item) for item in list(state.get("disease_candidates", []) or [])],
            "referral_required": bool(state.get("referral_required")),
            "disease_match_summary": str(state.get("disease_match_summary", "") or ""),
            "otc_candidates": [to_dict(item) for item in list(state.get("otc_candidates", []) or [])],
            "candidate_safety_results": [
                to_dict(item) for item in list(state.get("candidate_safety_results", []) or [])
            ],
            "medication_debate_summary": to_dict(state.get("medication_debate_summary")),
            "debate_results": [to_dict(item) for item in list(state.get("debate_results", []) or [])],
            "consult_report": str(state.get("consult_report", "") or ""),
        }
        return build_success_response(
            data=data,
            metadata={
                "engine_version": self.ENGINE_VERSION,
                "workflow_type": "symptom_consult",
                "symptom_agents_executed": executed + ["safety-guard-agent"],
                "symptom_agents_failed": failed,
                "red_flag_triggered": red_flag_triggered,
                "disease_library_used": bool(state.get("disease_library_used")),
                "disease_candidate_count": len(list(state.get("disease_candidates", []) or [])),
                "referral_required": bool(state.get("referral_required")),
                "safety_warning_count": len(list(state.get("safety_warnings", []) or [])),
                "debate_enabled": bool(state.get("debate_results"))
                and not red_flag_triggered
                and not bool(state.get("referral_required")),
                "debate_agents_executed": [name for name in executed if name in self.debate_agents],
                "debate_agents_failed": [name for name in failed if name in self.debate_agents],
            },
            message="症状问诊辅助检查完成",
        )

    @staticmethod
    def _sanitize_payload(payload: dict) -> dict:
        return {
            "symptom_text": str(payload.get("symptom_text", "") or ""),
            "age": payload.get("age"),
            "sex": payload.get("sex"),
            "temperature_c": payload.get("temperature_c"),
            "duration_days": payload.get("duration_days"),
            "current_drugs": list(payload.get("current_drugs", []) or []),
            "diseases": list(payload.get("diseases", []) or []),
            "patient_factors": list(payload.get("patient_factors", []) or []),
            "allergies": list(payload.get("allergies", []) or []),
            "dose": payload.get("dose"),
        }
