from fastapi.testclient import TestClient
from unittest.mock import patch

from medical_drug_agent.app.api.main import app


client = TestClient(app)


def _payload() -> dict:
    return {
        "current_drugs": ["硝苯地平"],
        "new_drug": "布洛芬",
        "age": 68,
        "diseases": ["高血压"],
        "patient_factors": [],
        "dose": None,
    }


def test_health_returns_200() -> None:
    response = client.get("/health")
    assert response.status_code == 200


def test_version_returns_200() -> None:
    response = client.get("/api/v1/version")
    assert response.status_code == 200


def test_drug_options_returns_success() -> None:
    response = client.get("/api/v1/drugs/options")
    payload = response.json()
    assert response.status_code == 200
    assert payload["status"] == "success"
    assert payload["data"]["options"]
    assert "display_name" in payload["data"]["options"][0]


def test_symptom_consult_returns_disease_candidates() -> None:
    response = client.post(
        "/api/v1/symptom-consult/check",
        json={
            "symptom_text": "发热、头痛、咽痛，两天了",
            "age": 30,
            "sex": "unknown",
            "temperature_c": 38.5,
            "duration_days": 2,
            "current_drugs": [],
            "diseases": [],
            "patient_factors": [],
            "allergies": [],
        },
    )
    payload = response.json()
    assert response.status_code == 200
    assert payload["status"] == "success"
    assert payload["data"]["disease_candidates"]
    assert "disease_candidate_count" in payload["metadata"]


def test_cors_preflight_allows_vue_localhost() -> None:
    response = client.options(
        "/api/v1/drug-safety/check",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "POST",
        },
    )
    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://localhost:5173"


def test_cors_preflight_allows_vue_preview_localhost() -> None:
    response = client.options(
        "/api/v1/drug-safety/check",
        headers={
            "Origin": "http://localhost:4173",
            "Access-Control-Request-Method": "POST",
        },
    )
    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://localhost:4173"


def test_default_case_returns_success() -> None:
    response = client.post("/api/v1/drug-safety/check", json=_payload())
    payload = response.json()
    assert response.status_code == 200
    assert payload["status"] == "success"


def test_response_has_required_top_level_fields() -> None:
    response = client.post("/api/v1/drug-safety/check", json=_payload())
    payload = response.json()
    for key in ["request_id", "timestamp", "status", "error_code", "message", "data", "metadata"]:
        assert key in payload


def test_data_contains_core_fields() -> None:
    response = client.post("/api/v1/drug-safety/check", json=_payload())
    data = response.json()["data"]
    for key in ["overall_risk_level", "pharmacist_report", "patient_report", "risk_findings", "dose_results"]:
        assert key in data


def test_reference_dose_mode_returns_label_reference_metadata() -> None:
    payload = _payload()
    payload["dose"] = {"dose_mode": "label_reference"}
    response = client.post("/api/v1/drug-safety/check", json=payload)
    dose_result = response.json()["data"]["dose_results"][0]
    assert response.status_code == 200
    assert dose_result["dose_source"] == "label_reference"
    assert dose_result["dose_assumption_used"] is True


def test_response_contains_audit_metadata() -> None:
    response = client.post("/api/v1/drug-safety/check", json=_payload())
    metadata = response.json()["metadata"]
    assert "audit" in metadata
    assert metadata["audit"]["logged"] is True
    assert metadata["audit"]["audit_id"]


def test_empty_current_drugs_returns_invalid_input() -> None:
    payload = _payload()
    payload["current_drugs"] = []
    response = client.post("/api/v1/drug-safety/check", json=payload)
    result = response.json()
    assert result["status"] == "error"
    assert result["error_code"] == "INVALID_INPUT"


def test_unknown_drug_returns_unknown_drug() -> None:
    payload = _payload()
    payload["current_drugs"] = ["未知药物"]
    response = client.post("/api/v1/drug-safety/check", json=payload)
    result = response.json()
    assert result["status"] == "error"
    assert result["error_code"] == "UNKNOWN_DRUG"


def test_multi_agent_route_returns_success() -> None:
    response = client.post("/api/v1/drug-safety/check?use_multi_agent=true", json=_payload())
    payload = response.json()
    assert response.status_code == 200
    assert payload["status"] == "success"
    assert "multi_agent" in payload["metadata"]
    assert payload["metadata"]["multi_agent"]["llm_enabled"] is True
    assert payload["metadata"]["configured_knowledge_backend"] in {"auto", "csv", "neo4j"}
    assert payload["metadata"]["active_knowledge_backend"] in {"csv", "neo4j"}


def test_multi_agent_route_enable_llm_false_can_disable() -> None:
    response = client.post("/api/v1/drug-safety/check?use_multi_agent=true&enable_llm=false", json=_payload())
    payload = response.json()
    assert response.status_code == 200
    assert payload["status"] == "success"
    assert payload["metadata"]["multi_agent"]["llm_enabled"] is False


def test_multi_agent_enable_llm_without_key_still_returns_success() -> None:
    response = client.post("/api/v1/drug-safety/check?use_multi_agent=true&enable_llm=true", json=_payload())
    payload = response.json()
    assert response.status_code == 200
    assert payload["status"] == "success"
    assert payload["metadata"]["multi_agent"]["llm_enabled"] is True


def test_multi_agent_route_accepts_knowledge_backend_override_csv() -> None:
    response = client.post("/api/v1/drug-safety/check?use_multi_agent=true&knowledge_backend=csv", json=_payload())
    payload = response.json()
    assert response.status_code == 200
    assert payload["status"] == "success"
    assert payload["metadata"]["configured_knowledge_backend"] == "csv"
    assert payload["metadata"]["active_knowledge_backend"] == "csv"
    assert payload["metadata"]["knowledge_backend"] == "csv"


def test_multi_agent_route_accepts_knowledge_backend_override_auto() -> None:
    response = client.post("/api/v1/drug-safety/check?use_multi_agent=true&knowledge_backend=auto", json=_payload())
    payload = response.json()
    assert response.status_code == 200
    assert payload["status"] == "success"
    assert payload["metadata"]["configured_knowledge_backend"] == "auto"
    assert payload["metadata"]["knowledge_backend"] in {"csv", "neo4j"}
    assert "fallback_used" in payload["metadata"]


def test_multi_agent_route_neo4j_override_returns_structured_backend_metadata() -> None:
    response = client.post("/api/v1/drug-safety/check?use_multi_agent=true&knowledge_backend=neo4j", json=_payload())
    payload = response.json()
    assert response.status_code == 200
    assert payload["status"] in {"success", "error"}
    assert "knowledge_backend" in payload["metadata"]
    assert "active_knowledge_backend" in payload["metadata"]
    assert "fallback_used" in payload["metadata"]


def test_kg_backend_status_returns_success() -> None:
    response = client.get("/api/v1/kg/backend-status")
    payload = response.json()
    assert response.status_code == 200
    assert payload["status"] == "success"
    assert payload["data"]["configured_knowledge_backend"] in {"auto", "csv", "neo4j"}
    assert payload["data"]["active_knowledge_backend"] in {"csv", "neo4j"}
    assert "fallback_used" in payload["data"]


def test_kg_backend_status_mock_connected_reports_neo4j() -> None:
    from medical_drug_agent.app.api import routes

    class FakeRouter:
        def __init__(self, backend=None) -> None:
            self.backend = backend

        def get_status(self) -> dict:
            return {
                "configured_backend": "auto",
                "active_backend": "neo4j",
                "configured_knowledge_backend": "auto",
                "active_knowledge_backend": "neo4j",
                "knowledge_backend": "neo4j",
                "neo4j_configured": True,
                "neo4j_connected": True,
                "neo4j_version": "5.20.0",
                "fallback_available": True,
                "fallback_used": False,
                "fallback_reason": None,
            }

    with patch.object(routes, "KnowledgeBackendRouter", FakeRouter):
        response = client.get("/api/v1/kg/backend-status?knowledge_backend=auto")
        payload = response.json()

    assert response.status_code == 200
    assert payload["status"] == "success"
    assert payload["data"]["active_backend"] == "neo4j"
    assert payload["data"]["neo4j_connected"] is True
    assert payload["data"]["fallback_used"] is False


def test_kg_backend_status_mock_disconnected_reports_csv_fallback() -> None:
    from medical_drug_agent.app.api import routes

    class FakeRouter:
        def __init__(self, backend=None) -> None:
            self.backend = backend

        def get_status(self) -> dict:
            return {
                "configured_backend": "auto",
                "active_backend": "csv",
                "configured_knowledge_backend": "auto",
                "active_knowledge_backend": "csv",
                "knowledge_backend": "csv",
                "neo4j_configured": True,
                "neo4j_connected": False,
                "neo4j_version": None,
                "fallback_available": True,
                "fallback_used": True,
                "fallback_reason": "mock neo4j unavailable",
            }

    with patch.object(routes, "KnowledgeBackendRouter", FakeRouter):
        response = client.get("/api/v1/kg/backend-status?knowledge_backend=auto")
        payload = response.json()

    assert response.status_code == 200
    assert payload["status"] == "success"
    assert payload["data"]["active_backend"] == "csv"
    assert payload["data"]["neo4j_connected"] is False
    assert payload["data"]["fallback_used"] is True
    assert payload["data"]["fallback_reason"] == "mock neo4j unavailable"
