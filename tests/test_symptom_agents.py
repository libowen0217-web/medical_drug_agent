from medical_drug_agent.app.agents import AgentResult
from medical_drug_agent.app.agents.candidate_safety_agent import CandidateSafetyAgent
from medical_drug_agent.app.agents.otc_candidate_agent import OTCCandidateAgent
from medical_drug_agent.app.agents.red_flag_check_agent import RedFlagCheckAgent
from medical_drug_agent.app.agents.symptom_consult_report_agent import SymptomConsultReportAgent
from medical_drug_agent.app.agents.symptom_intake_agent import SymptomIntakeAgent
from medical_drug_agent.app.symptom.schemas import OTCCandidate


def _payload() -> dict:
    return {
        "symptom_text": "发热、头痛、嗓子疼，两天了",
        "age": 68,
        "sex": "unknown",
        "temperature_c": 38.5,
        "duration_days": 2,
        "current_drugs": ["硝苯地平"],
        "diseases": ["高血压"],
        "patient_factors": [],
        "allergies": [],
    }


def test_symptom_intake_agent_returns_agent_result() -> None:
    result = SymptomIntakeAgent().run({"input_payload": _payload()})
    assert isinstance(result, AgentResult)
    assert result.status == "success"


def test_red_flag_check_agent_can_set_stop_flag() -> None:
    payload = _payload()
    payload["symptom_text"] = "胸痛，呼吸困难"
    result = RedFlagCheckAgent().run({"input_payload": payload})
    assert result.output["stop_candidate_recommendation"] is True


def test_otc_candidate_agent_skips_on_red_flag() -> None:
    result = OTCCandidateAgent().run({"stop_candidate_recommendation": True})
    assert result.status == "skipped"


def test_candidate_safety_agent_can_call_existing_safety_chain() -> None:
    state = {
        "input_payload": _payload(),
        "otc_candidates": [
            OTCCandidate(
                candidate_id="x",
                symptom_group="发热疼痛",
                drug_class="退热镇痛类",
                candidate_drugs=["对乙酰氨基酚"],
                is_otc=True,
                requires_doctor_confirmation=False,
                caution="",
                reason="",
            )
        ],
    }
    result = CandidateSafetyAgent().run(state)
    assert result.status == "success"
    assert result.output["candidate_safety_results"]


def test_candidate_safety_agent_without_current_drugs_uses_reference_dose() -> None:
    state = {
        "input_payload": {
            **_payload(),
            "current_drugs": [],
            "dose": None,
        },
        "otc_candidates": [
            OTCCandidate(
                candidate_id="x",
                symptom_group="发热疼痛",
                drug_class="退热镇痛类",
                candidate_drugs=["布洛芬"],
                is_otc=True,
                requires_doctor_confirmation=False,
                caution="",
                reason="",
            )
        ],
    }
    result = CandidateSafetyAgent().run(state)
    data = result.output["candidate_safety_results"][0].safety_response["data"]
    dose_result = data["dose_results"][0]
    assert result.status == "success"
    assert dose_result["dose_source"] == "label_reference"
    assert dose_result["dose_assumption_used"] is True
    assert "不代表患者实际用药剂量" in dose_result["message"]


def test_symptom_consult_report_agent_generates_report() -> None:
    state = {
        "input_payload": _payload(),
        "parsed_symptoms": [],
        "red_flags": [],
        "otc_candidates": [],
        "candidate_safety_results": [],
    }
    result = SymptomConsultReportAgent().run(state)
    assert result.status == "success"
    assert result.output["consult_report"]
