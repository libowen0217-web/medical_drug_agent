from medical_drug_agent.app.service import DrugSafetyService


def _payload() -> dict:
    return {
        "current_drugs": ["Nifedipine"],
        "new_drug": "Ibuprofen",
        "age": 68,
        "diseases": ["高血压"],
        "patient_factors": [],
        "dose": None,
    }


def test_service_risk_findings_include_evidence_items() -> None:
    response = DrugSafetyService().check_from_dict(_payload())
    assert response["data"]["risk_findings"]
    assert "evidence_items" in response["data"]["risk_findings"][0]
    assert "score" in response["data"]["risk_findings"][0]["evidence_items"][0]
    assert "citation_label" in response["data"]["risk_findings"][0]["evidence_items"][0]
    assert "rank" in response["data"]["risk_findings"][0]["evidence_items"][0]


def test_hypertension_ibuprofen_rule_finding_has_evidence() -> None:
    response = DrugSafetyService().check_from_dict(_payload())
    findings = response["data"]["risk_findings"]
    matched = [finding for finding in findings if "血压" in finding["title"] or "高血压" in finding["description"]]
    assert matched
    assert matched[0]["evidence_items"]


def test_pharmacist_report_contains_evidence_prompt_or_source_name() -> None:
    response = DrugSafetyService().check_from_dict(_payload())
    report = response["data"]["pharmacist_report"]
    assert "证据提示" in report
    assert "[证据1]" in report


def test_langgraph_path_also_returns_evidence_items() -> None:
    response = DrugSafetyService(use_graph=True).check_from_dict(_payload())
    assert response["data"]["risk_findings"]
    assert "evidence_items" in response["data"]["risk_findings"][0]
    assert response["data"]["risk_findings"][0]["evidence_items"][0]["citation_label"]
