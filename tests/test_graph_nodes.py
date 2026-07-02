from medical_drug_agent.app.graph.nodes import (
    build_response_node,
    dose_check_node,
    normalize_drugs_node,
    query_kg_node,
    validate_input_node,
)


def test_validate_input_node_accepts_valid_payload() -> None:
    state = validate_input_node(
        {
            "input_payload": {
                "current_drugs": ["Nifedipine"],
                "new_drug": "Ibuprofen",
                "age": 68,
                "diseases": ["高血压"],
                "patient_factors": [],
                "dose": None,
            }
        }
    )
    assert state.get("error") is None
    assert state["current_drug_inputs"] == ["Nifedipine"]


def test_validate_input_node_rejects_empty_current_drugs() -> None:
    state = validate_input_node({"input_payload": {"current_drugs": [], "new_drug": "Ibuprofen"}})
    assert state["error"]["error_code"] == "INVALID_INPUT"


def test_normalize_drugs_node_normalizes_ibuprofen() -> None:
    state = normalize_drugs_node(
        {
            "current_drug_inputs": ["Nifedipine"],
            "new_drug_input": "布洛芬",
            "age": 68,
            "diseases": ["高血压"],
            "patient_factors": [],
        }
    )
    assert state["normalized_new_drug"].en_name == "Ibuprofen"


def test_query_kg_node_returns_pair_relations() -> None:
    state = query_kg_node(
        {
            "current_drug_inputs": ["Nifedipine"],
            "new_drug_input": "Ibuprofen",
        }
    )
    assert "kg_pair_relations" in state
    assert "kg_query_summary" in state


def test_dose_check_node_returns_missing_dose_when_absent() -> None:
    state = dose_check_node({"new_drug_input": "Ibuprofen", "dose": None})
    assert state["dose_results"][0].status == "missing_dose"


def test_build_response_node_generates_success_response() -> None:
    normalized_state = normalize_drugs_node(
        {
            "current_drug_inputs": ["Nifedipine"],
            "new_drug_input": "Ibuprofen",
            "age": 68,
            "diseases": ["高血压"],
            "patient_factors": [],
        }
    )
    normalized_state["risk_summary"] = type(
        "RiskSummaryStub",
        (),
        {"overall_risk_level": "medium", "findings": []},
    )()
    normalized_state["pharmacist_report"] = "药师报告"
    normalized_state["patient_report"] = "患者报告"
    normalized_state["safety_warnings"] = []
    normalized_state["kg_query_summary"] = {"relation_count": 0}
    state = build_response_node(normalized_state)
    assert state["response"]["status"] == "success"


def test_build_response_node_generates_error_response() -> None:
    state = build_response_node({"error": {"error_code": "INVALID_INPUT", "message": "bad input"}})
    assert state["response"]["status"] == "error"
    assert state["response"]["error_code"] == "INVALID_INPUT"
