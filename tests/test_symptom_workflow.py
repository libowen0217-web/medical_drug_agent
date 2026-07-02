from fastapi.testclient import TestClient

from medical_drug_agent.app.api.main import app
from medical_drug_agent.app.symptom.symptom_workflow import SymptomConsultWorkflow


DEFAULT_PAYLOAD = {
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

RED_FLAG_PAYLOAD = {
    "symptom_text": "发烧40度，胸痛，呼吸困难，意识有点模糊",
    "age": 70,
    "sex": "unknown",
    "temperature_c": 40.0,
    "duration_days": 1,
    "current_drugs": ["硝苯地平"],
    "diseases": ["高血压"],
    "patient_factors": ["老年人"],
    "allergies": [],
}

EMPTY_CURRENT_DRUGS_PAYLOAD = {
    "symptom_text": "头痛，一天了",
    "age": 30,
    "sex": "female",
    "temperature_c": 36.8,
    "duration_days": 1,
    "current_drugs": [],
    "diseases": [],
    "patient_factors": [],
    "allergies": [],
    "dose": None,
}

SERIOUS_DISEASE_PAYLOAD = {
    "symptom_text": "胸痛，伴呼吸困难，最近还有咯血",
    "age": 70,
    "sex": "unknown",
    "temperature_c": 37.2,
    "duration_days": 7,
    "current_drugs": ["硝苯地平"],
    "diseases": ["高血压"],
    "patient_factors": ["老年人"],
    "allergies": [],
    "dose": None,
}


def test_default_symptom_case_returns_success() -> None:
    response = SymptomConsultWorkflow().run(DEFAULT_PAYLOAD)
    assert response["status"] == "success"


def test_default_case_has_parsed_symptoms() -> None:
    data = SymptomConsultWorkflow().run(DEFAULT_PAYLOAD)["data"]
    assert data["parsed_symptoms"]


def test_default_case_has_otc_candidates() -> None:
    data = SymptomConsultWorkflow().run(DEFAULT_PAYLOAD)["data"]
    assert data["otc_candidates"]


def test_default_case_has_disease_candidates() -> None:
    data = SymptomConsultWorkflow().run({**DEFAULT_PAYLOAD, "symptom_text": "发热、头痛、咽痛，两天了"})["data"]
    assert data["disease_candidates"]
    assert data["referral_required"] is False


def test_lung_cancer_case_requires_referral_without_otc_candidates() -> None:
    payload = {**DEFAULT_PAYLOAD, "symptom_text": "肺癌"}
    response = SymptomConsultWorkflow().run(payload)
    assert response["status"] == "success"
    assert response["data"]["referral_required"] is True
    assert response["data"]["otc_candidates"] == []
    assert response["data"]["candidate_safety_results"] == []


def test_chest_pain_case_blocks_candidates() -> None:
    payload = {**DEFAULT_PAYLOAD, "symptom_text": "胸痛"}
    response = SymptomConsultWorkflow().run(payload)
    assert response["status"] == "success"
    assert response["data"]["otc_candidates"] == []


def test_default_case_has_candidate_safety_results() -> None:
    data = SymptomConsultWorkflow().run(DEFAULT_PAYLOAD)["data"]
    assert data["candidate_safety_results"]


def test_default_case_has_medication_debate_summary() -> None:
    data = SymptomConsultWorkflow().run(DEFAULT_PAYLOAD)["data"]
    assert data["medication_debate_summary"]


def test_default_case_has_debate_results() -> None:
    data = SymptomConsultWorkflow().run(DEFAULT_PAYLOAD)["data"]
    assert data["debate_results"]


def test_debate_results_include_rank() -> None:
    data = SymptomConsultWorkflow().run(DEFAULT_PAYLOAD)["data"]
    assert data["debate_results"][0]["rank"] >= 1


def test_red_flag_case_returns_red_flag_triggered_true() -> None:
    response = SymptomConsultWorkflow().run(RED_FLAG_PAYLOAD)
    assert response["metadata"]["red_flag_triggered"] is True


def test_red_flag_case_has_empty_otc_candidates() -> None:
    data = SymptomConsultWorkflow().run(RED_FLAG_PAYLOAD)["data"]
    assert data["otc_candidates"] == []


def test_red_flag_case_has_empty_candidate_safety_results() -> None:
    data = SymptomConsultWorkflow().run(RED_FLAG_PAYLOAD)["data"]
    assert data["candidate_safety_results"] == []


def test_red_flag_case_has_empty_debate_results() -> None:
    data = SymptomConsultWorkflow().run(RED_FLAG_PAYLOAD)["data"]
    assert data["debate_results"] == []


def test_red_flag_case_summary_marks_blocked() -> None:
    data = SymptomConsultWorkflow().run(RED_FLAG_PAYLOAD)["data"]
    assert data["medication_debate_summary"]["red_flag_blocked"] is True


def test_serious_disease_case_triggers_block() -> None:
    response = SymptomConsultWorkflow().run(SERIOUS_DISEASE_PAYLOAD)
    assert response["metadata"]["red_flag_triggered"] is True
    assert response["data"]["otc_candidates"] == []


def test_empty_current_drugs_still_generates_otc_candidates() -> None:
    data = SymptomConsultWorkflow().run(EMPTY_CURRENT_DRUGS_PAYLOAD)["data"]
    assert data["otc_candidates"]


def test_empty_current_drugs_still_generates_candidate_safety_results() -> None:
    data = SymptomConsultWorkflow().run(EMPTY_CURRENT_DRUGS_PAYLOAD)["data"]
    assert data["candidate_safety_results"]
    assert data["candidate_safety_results"][0]["safety_response"]["status"] == "success"


def test_empty_current_drugs_candidate_safety_uses_reference_dose() -> None:
    data = SymptomConsultWorkflow().run(EMPTY_CURRENT_DRUGS_PAYLOAD)["data"]
    dose_result = data["candidate_safety_results"][0]["safety_response"]["data"]["dose_results"][0]
    assert dose_result["dose_source"] == "label_reference"
    assert dose_result["dose_assumption_used"] is True
    assert "不代表患者实际用药剂量" in dose_result["message"]


def test_empty_current_drugs_report_explains_ddi_not_checked() -> None:
    report = SymptomConsultWorkflow().run(EMPTY_CURRENT_DRUGS_PAYLOAD)["data"]["consult_report"]
    assert "未提供当前用药" in report


def test_consult_report_contains_debate_section() -> None:
    report = SymptomConsultWorkflow().run(DEFAULT_PAYLOAD)["data"]["consult_report"]
    assert "候选药协作评估" in report


def test_consult_report_contains_reference_dose_disclaimer_when_dose_missing() -> None:
    report = SymptomConsultWorkflow().run(EMPTY_CURRENT_DRUGS_PAYLOAD)["data"]["consult_report"]
    assert "说明书参考剂量" in report
    assert "不代表患者实际用药剂量" in report


def test_consult_report_avoids_forbidden_phrases() -> None:
    report = SymptomConsultWorkflow().run(DEFAULT_PAYLOAD)["data"]["consult_report"]
    assert "应该吃" not in report
    assert "可以吃" not in report
    assert "放心服用" not in report


def test_fastapi_symptom_consult_route_returns_success() -> None:
    client = TestClient(app)
    response = client.post("/api/v1/symptom-consult/check", json=DEFAULT_PAYLOAD)
    payload = response.json()
    assert response.status_code == 200
    assert payload["status"] == "success"
