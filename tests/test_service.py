from medical_drug_agent.app.schemas import DrugSafetyRequest
from medical_drug_agent.app.service import DrugSafetyService


def test_default_case_returns_success() -> None:
    service = DrugSafetyService()
    response = service.check(
        DrugSafetyRequest(
            current_drugs=["硝苯地平"],
            new_drug="布洛芬",
            age=68,
            diseases=["高血压"],
            patient_factors=[],
            dose=None,
        )
    )
    assert response.status == "success"


def test_data_contains_core_fields() -> None:
    service = DrugSafetyService()
    response = service.check(
        DrugSafetyRequest(
            current_drugs=["硝苯地平"],
            new_drug="布洛芬",
            age=68,
            diseases=["高血压"],
        )
    )
    assert response.data is not None
    assert "pharmacist_report" in response.data
    assert "patient_report" in response.data
    assert "risk_findings" in response.data
    assert "overall_risk_level" in response.data
    assert response.metadata["engine_version"] == "local-csv-mvp-v1"


def test_empty_current_drugs_returns_invalid_input() -> None:
    service = DrugSafetyService()
    response = service.check(DrugSafetyRequest(current_drugs=[], new_drug="布洛芬"))
    assert response.status == "error"
    assert response.error_code == "INVALID_INPUT"


def test_empty_new_drug_returns_invalid_input() -> None:
    service = DrugSafetyService()
    response = service.check(DrugSafetyRequest(current_drugs=["硝苯地平"], new_drug=""))
    assert response.status == "error"
    assert response.error_code == "INVALID_INPUT"


def test_unknown_drug_returns_unknown_drug() -> None:
    service = DrugSafetyService()
    response = service.check(DrugSafetyRequest(current_drugs=["未知药物"], new_drug="布洛芬"))
    assert response.status == "error"
    assert response.error_code == "UNKNOWN_DRUG"


def test_negative_age_returns_invalid_input() -> None:
    service = DrugSafetyService()
    response = service.check(
        DrugSafetyRequest(current_drugs=["硝苯地平"], new_drug="布洛芬", age=-1)
    )
    assert response.status == "error"
    assert response.error_code == "INVALID_INPUT"
