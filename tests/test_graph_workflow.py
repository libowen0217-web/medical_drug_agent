from fastapi.testclient import TestClient

from medical_drug_agent.app.api.main import app
from medical_drug_agent.app.graph.graph import DrugSafetyLangGraph
from medical_drug_agent.app.service import DrugSafetyService


client = TestClient(app)


def test_langgraph_default_case_returns_success() -> None:
    response = DrugSafetyLangGraph().run(
        {
            "current_drugs": ["Nifedipine"],
            "new_drug": "Ibuprofen",
            "age": 68,
            "diseases": ["高血压"],
            "patient_factors": [],
            "dose": None,
        }
    )
    assert response["status"] == "success"


def test_langgraph_response_contains_required_fields() -> None:
    response = DrugSafetyLangGraph().run(
        {
            "current_drugs": ["Nifedipine"],
            "new_drug": "Ibuprofen",
            "age": 68,
            "diseases": ["高血压"],
            "patient_factors": [],
            "dose": None,
        }
    )
    for key in ["request_id", "timestamp", "status", "error_code", "message", "data", "metadata"]:
        assert key in response


def test_langgraph_data_contains_core_fields() -> None:
    response = DrugSafetyLangGraph().run(
        {
            "current_drugs": ["Nifedipine"],
            "new_drug": "Ibuprofen",
            "age": 68,
            "diseases": ["高血压"],
            "patient_factors": [],
            "dose": None,
        }
    )
    assert "overall_risk_level" in response["data"]
    assert "pharmacist_report" in response["data"]
    assert "patient_report" in response["data"]


def test_langgraph_unknown_drug_returns_error() -> None:
    response = DrugSafetyLangGraph().run(
        {
            "current_drugs": ["Nifedipine"],
            "new_drug": "UnknownDrug",
            "age": 68,
            "diseases": ["高血压"],
            "patient_factors": [],
            "dose": None,
        }
    )
    assert response["status"] == "error"


def test_langgraph_empty_current_drugs_returns_error() -> None:
    response = DrugSafetyLangGraph().run(
        {
            "current_drugs": [],
            "new_drug": "Ibuprofen",
            "age": 68,
            "diseases": ["高血压"],
            "patient_factors": [],
            "dose": None,
        }
    )
    assert response["status"] == "error"


def test_service_use_graph_path_runs() -> None:
    response = DrugSafetyService(use_graph=True).check_from_dict(
        {
            "current_drugs": ["Nifedipine"],
            "new_drug": "Ibuprofen",
            "age": 68,
            "diseases": ["高血压"],
            "patient_factors": [],
            "dose": None,
        }
    )
    assert response["status"] == "success"


def test_fastapi_use_graph_query_works() -> None:
    response = client.post(
        "/api/v1/drug-safety/check?use_graph=true",
        json={
            "current_drugs": ["Nifedipine"],
            "new_drug": "Ibuprofen",
            "age": 68,
            "diseases": ["高血压"],
            "patient_factors": [],
            "dose": None,
        },
    )
    assert response.status_code == 200
    assert response.json()["status"] == "success"
