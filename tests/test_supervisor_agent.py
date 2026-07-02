import os
from unittest.mock import patch

from medical_drug_agent.app.agents.supervisor_agent import SupervisorAgent


def _payload(dose: dict | None = None) -> dict:
    return {
        "current_drugs": ["硝苯地平"],
        "new_drug": "布洛芬",
        "age": 68,
        "diseases": ["高血压"],
        "patient_factors": [],
        "dose": dose,
    }


def test_supervisor_agent_default_case_returns_success() -> None:
    response = SupervisorAgent().run(_payload())
    assert response["status"] == "success"


def test_supervisor_agent_matches_api_ready_contract() -> None:
    response = SupervisorAgent().run(_payload())
    for key in ["request_id", "timestamp", "status", "error_code", "message", "data", "metadata"]:
        assert key in response


def test_supervisor_agent_success_data_contains_core_fields() -> None:
    response = SupervisorAgent().run(_payload())
    data = response["data"]
    assert "overall_risk_level" in data
    assert "pharmacist_report" in data
    assert "patient_report" in data


def test_supervisor_agent_metadata_contains_multi_agent() -> None:
    response = SupervisorAgent().run(_payload())
    multi_agent = response["metadata"]["multi_agent"]
    assert multi_agent["enabled"] is True
    assert multi_agent["execution_mode"] == "multi-agent"
    assert response["metadata"]["configured_knowledge_backend"] in {"auto", "csv", "neo4j"}
    assert response["metadata"]["active_knowledge_backend"] in {"csv", "neo4j"}


def test_supervisor_agent_agents_executed_contains_multiple_agents() -> None:
    response = SupervisorAgent().run(_payload())
    executed = response["metadata"]["multi_agent"]["agents_executed"]
    assert "drug-normalization-agent" in executed
    assert "safety-guard-agent" in executed


def test_supervisor_agent_agents_failed_empty_on_success() -> None:
    response = SupervisorAgent().run(_payload())
    assert response["metadata"]["multi_agent"]["agents_failed"] == []


def test_supervisor_agent_default_enables_llm() -> None:
    response = SupervisorAgent().run(_payload())
    assert response["metadata"]["multi_agent"]["llm_enabled"] is True


def test_supervisor_agent_enable_llm_false_can_disable() -> None:
    response = SupervisorAgent(enable_llm=False).run(_payload())
    assert response["metadata"]["multi_agent"]["llm_enabled"] is False
    assert response["metadata"]["multi_agent"]["llm_used"] is False


def test_supervisor_agent_enable_llm_true_can_run() -> None:
    response = SupervisorAgent(enable_llm=True).run(_payload())
    assert response["status"] == "success"


def test_supervisor_agent_without_llm_key_still_returns_success() -> None:
    response = SupervisorAgent(enable_llm=True).run(_payload())
    assert response["status"] == "success"


def test_supervisor_agent_without_llm_key_marks_llm_used_false() -> None:
    with patch.dict(os.environ, {"LLM_API_KEY": "", "LLM_BASE_URL": "", "LLM_MODEL": ""}, clear=False):
        response = SupervisorAgent(enable_llm=True).run(_payload())
    assert response["metadata"]["multi_agent"]["llm_used"] is False


def test_supervisor_agent_default_llm_failure_falls_back_without_crashing() -> None:
    response = SupervisorAgent().run(_payload())
    assert response["status"] == "success"
    assert response["metadata"]["multi_agent"]["llm_enabled"] is True
    assert "pharmacist_report" in response["data"]
    assert "patient_report" in response["data"]


def test_supervisor_agent_agents_executed_contains_llm_report_agent_when_enabled() -> None:
    response = SupervisorAgent(enable_llm=True).run(_payload())
    assert "llm-report-agent" in response["metadata"]["multi_agent"]["agents_executed"]


def test_safety_guard_agent_runs_after_llm_report_agent() -> None:
    response = SupervisorAgent(enable_llm=True).run(_payload())
    executed = response["metadata"]["multi_agent"]["agents_executed"]
    assert executed.index("llm-report-agent") < executed.index("safety-guard-agent")


def test_supervisor_agent_unknown_drug_returns_error() -> None:
    response = SupervisorAgent().run(
        {
            "current_drugs": ["未知药物"],
            "new_drug": "布洛芬",
            "age": 68,
            "diseases": ["高血压"],
            "patient_factors": [],
            "dose": None,
        }
    )
    assert response["status"] == "error"
    assert response["error_code"] == "UNKNOWN_DRUG"


def test_supervisor_agent_unknown_drug_has_failed_agent() -> None:
    response = SupervisorAgent().run(
        {
            "current_drugs": ["未知药物"],
            "new_drug": "布洛芬",
            "age": 68,
            "diseases": ["高血压"],
            "patient_factors": [],
            "dose": None,
        }
    )
    assert response["metadata"]["multi_agent"]["agents_failed"]
