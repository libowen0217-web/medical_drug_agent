from medical_drug_agent.app.api_contract import build_error_response, build_success_response


def test_success_response_contains_request_id() -> None:
    response = build_success_response(data={}, metadata={})
    assert response["request_id"]


def test_success_response_contains_timestamp() -> None:
    response = build_success_response(data={}, metadata={})
    assert response["timestamp"]


def test_success_response_has_required_top_level_fields() -> None:
    response = build_success_response(data={"overall_risk_level": "medium"}, metadata={})
    assert set(["status", "error_code", "message", "data", "metadata"]).issubset(response.keys())


def test_success_response_overall_risk_level_is_in_data() -> None:
    response = build_success_response(data={"overall_risk_level": "medium"}, metadata={})
    assert response["data"]["overall_risk_level"] == "medium"


def test_error_response_data_is_none() -> None:
    response = build_error_response(error_code="INVALID_INPUT", message="bad")
    assert response["data"] is None


def test_error_response_contains_error_code() -> None:
    response = build_error_response(error_code="INVALID_INPUT", message="bad")
    assert response["error_code"] == "INVALID_INPUT"


def test_request_id_is_non_empty_string() -> None:
    response = build_success_response(data={}, metadata={})
    assert isinstance(response["request_id"], str) and response["request_id"]


def test_timestamp_is_non_empty_string() -> None:
    response = build_success_response(data={}, metadata={})
    assert isinstance(response["timestamp"], str) and response["timestamp"]
