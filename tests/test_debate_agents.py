from medical_drug_agent.app.agents import AgentResult
from medical_drug_agent.app.agents.dose_reasoning_agent import DoseReasoningAgent
from medical_drug_agent.app.agents.evidence_review_agent import EvidenceReviewAgent
from medical_drug_agent.app.agents.interaction_risk_agent import InteractionRiskAgent
from medical_drug_agent.app.agents.medication_debate_manager_agent import MedicationDebateManagerAgent
from medical_drug_agent.app.agents.patient_factor_risk_agent import PatientFactorRiskAgent
from medical_drug_agent.app.agents.symptom_fit_agent import SymptomFitAgent
from medical_drug_agent.app.symptom.schemas import CandidateSafetyResult, OTCCandidate, ParsedSymptom


def _state() -> dict:
    return {
        "input_payload": {
            "symptom_text": "发热、头痛、嗓子疼，两天了",
            "age": 68,
            "diseases": ["高血压"],
            "patient_factors": [],
            "dose": None,
        },
        "parsed_symptoms": [ParsedSymptom(symptom_name="发热疼痛", matched_keywords=["发热", "头痛"])],
        "otc_candidates": [
            OTCCandidate(
                candidate_id="c1",
                symptom_group="发热疼痛",
                drug_class="解热镇痛类",
                candidate_drugs=["Ibuprofen", "Acetaminophen"],
                is_otc=True,
                requires_doctor_confirmation=False,
                caution="",
                reason="",
            )
        ],
        "candidate_safety_results": [
            CandidateSafetyResult(
                candidate_drug="Ibuprofen",
                safety_response={
                    "status": "success",
                    "data": {
                        "overall_risk_level": "medium",
                        "risk_findings": [
                            {
                                "source": "rule",
                                "risk_level": "medium",
                                "title": "NSAID 与高血压相关注意事项",
                                "description": "需要结合血压情况复核。",
                                "evidence_items": [{"citation_label": "[1]", "source_name": "local-evidence"}],
                            }
                        ],
                        "dose_results": [
                            {
                                "status": "label_reference",
                                "dose_source": "label_reference",
                                "dose_source_label": "说明书参考剂量",
                                "message": "本次基于说明书参考剂量进行了模拟评估，不代表患者实际用药剂量。",
                            }
                        ],
                    },
                },
            ),
            CandidateSafetyResult(
                candidate_drug="Acetaminophen",
                safety_response={
                    "status": "success",
                    "data": {"overall_risk_level": "low", "risk_findings": [], "dose_results": []},
                },
            ),
        ],
    }


def test_symptom_fit_agent_returns_agent_result() -> None:
    result = SymptomFitAgent().run(_state())
    assert isinstance(result, AgentResult)
    assert result.status == "success"


def test_interaction_risk_agent_outputs_opinions() -> None:
    result = InteractionRiskAgent().run(_state())
    assert result.status == "success"
    assert result.output["interaction_risk_opinions"]["Ibuprofen"]


def test_patient_factor_risk_agent_identifies_hypertension_ibuprofen() -> None:
    result = PatientFactorRiskAgent().run(_state())
    opinion = result.output["patient_factor_opinions"]["Ibuprofen"][0]
    assert any("高血压" in item for item in opinion.reasons)


def test_dose_reasoning_agent_identifies_reference_dose_message() -> None:
    result = DoseReasoningAgent().run(_state())
    opinion = result.output["dose_reasoning_opinions"]["Ibuprofen"][0]
    assert any("说明书参考剂量" in item or "不代表患者实际用药剂量" in item for item in opinion.reasons)


def test_evidence_review_agent_extracts_refs() -> None:
    result = EvidenceReviewAgent().run(_state())
    opinion = result.output["evidence_review_opinions"]["Ibuprofen"][0]
    assert opinion.evidence_refs == ["[1]"]


def test_medication_debate_manager_outputs_ranking_with_rank() -> None:
    state = _state()
    state.update(SymptomFitAgent().run(state).output or {})
    state.update(InteractionRiskAgent().run(state).output or {})
    state.update(PatientFactorRiskAgent().run(state).output or {})
    state.update(DoseReasoningAgent().run(state).output or {})
    state.update(EvidenceReviewAgent().run(state).output or {})
    result = MedicationDebateManagerAgent().run(state)
    assert result.status == "success"
    assert result.output["debate_results"]
    assert result.output["debate_results"][0].rank >= 1


def test_debate_output_avoids_forbidden_phrases() -> None:
    state = _state()
    state.update(SymptomFitAgent().run(state).output or {})
    state.update(InteractionRiskAgent().run(state).output or {})
    state.update(PatientFactorRiskAgent().run(state).output or {})
    state.update(DoseReasoningAgent().run(state).output or {})
    state.update(EvidenceReviewAgent().run(state).output or {})
    result = MedicationDebateManagerAgent().run(state)
    text = " ".join(item.summary for item in result.output["debate_results"])
    assert "可以吃" not in text
    assert "应该吃" not in text
    assert "放心服用" not in text
