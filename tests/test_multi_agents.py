from medical_drug_agent.app.agents import (
    AgentResult,
    DoseCheckAgent,
    DrugNormalizationAgent,
    KGQueryAgent,
    ReportAgent,
    RiskAggregationAgent,
    RuleCheckAgent,
    SafetyGuardAgent,
)


def _base_payload() -> dict:
    return {
        "current_drugs": ["硝苯地平"],
        "new_drug": "布洛芬",
        "age": 68,
        "diseases": ["高血压"],
        "patient_factors": [],
        "dose": None,
    }


def test_drug_normalization_agent_normalizes_ibuprofen() -> None:
    result = DrugNormalizationAgent().run({"input_payload": _base_payload()})
    assert result.status == "success"
    assert result.output["normalized_new_drug"].en_name == "Ibuprofen"


def test_kg_query_agent_returns_summary() -> None:
    state = DrugNormalizationAgent().run({"input_payload": _base_payload()}).output
    result = KGQueryAgent().run(state)
    assert result.status == "success"
    assert "kg_query_summary" in result.output


def test_rule_check_agent_matches_hypertension_nsaid_rule() -> None:
    state = {"input_payload": _base_payload()}
    state.update(DrugNormalizationAgent().run(state).output)
    result = RuleCheckAgent().run(state)
    assert result.status == "success"
    assert any(match.rule_id == "R001" for match in result.output["rule_matches"])


def test_dose_check_agent_returns_missing_dose_without_mode() -> None:
    state = {"input_payload": _base_payload()}
    state.update(DrugNormalizationAgent().run(state).output)
    result = DoseCheckAgent().run(state)
    assert result.status == "success"
    assert result.output["dose_results"][0].status == "missing_dose"
    assert result.output["dose_results"][0].dose_source == "missing"


def test_dose_check_agent_can_use_reference_mode_for_otc_new_drug() -> None:
    payload = _base_payload()
    payload["dose"] = {"dose_mode": "label_reference"}
    state = {"input_payload": payload}
    state.update(DrugNormalizationAgent().run(state).output)
    result = DoseCheckAgent().run(state)
    dose_result = result.output["dose_results"][0]
    assert result.status == "success"
    assert dose_result.dose_source == "label_reference"
    assert dose_result.dose_assumption_used is True


def test_risk_aggregation_agent_builds_risk_summary() -> None:
    state = {"input_payload": _base_payload()}
    state.update(DrugNormalizationAgent().run(state).output)
    state.update(KGQueryAgent().run(state).output)
    state.update(RuleCheckAgent().run(state).output)
    state.update(DoseCheckAgent().run(state).output)
    result = RiskAggregationAgent().run(state)
    assert result.status == "success"
    assert result.output["risk_summary"].overall_risk_level


def test_report_agent_creates_reports() -> None:
    state = {"input_payload": _base_payload()}
    state.update(DrugNormalizationAgent().run(state).output)
    state.update(KGQueryAgent().run(state).output)
    state.update(RuleCheckAgent().run(state).output)
    state.update(DoseCheckAgent().run(state).output)
    state.update(RiskAggregationAgent().run(state).output)
    result = ReportAgent().run(state)
    assert result.status == "success"
    assert result.output["pharmacist_report"]
    assert result.output["patient_report"]


def test_safety_guard_agent_filters_reports() -> None:
    state = {
        "pharmacist_report": "这个方案完全安全。",
        "patient_report": "你可以吃这个药。",
    }
    result = SafetyGuardAgent().run(state)
    assert result.status == "success"
    assert "完全安全" not in result.output["pharmacist_report"]
    assert "你可以吃" not in result.output["patient_report"]


def test_single_agent_returns_agent_result() -> None:
    result = DrugNormalizationAgent().run({"input_payload": _base_payload()})
    assert isinstance(result, AgentResult)
