import json

from medical_drug_agent.app.schemas import DrugInfo, DrugSafetyRequest, RiskFinding, RiskSummary
from medical_drug_agent.app.serialization import to_dict, to_json


def test_dataclass_can_convert_to_dict() -> None:
    request = DrugSafetyRequest(current_drugs=["硝苯地平"], new_drug="布洛芬")
    result = to_dict(request)
    assert result["new_drug"] == "布洛芬"


def test_nested_list_and_dataclass_can_convert_to_dict() -> None:
    summary = RiskSummary(
        overall_risk_level="medium",
        findings=[
            RiskFinding(
                source="rule_match",
                risk_level="medium",
                title="可能影响血压控制",
                description="desc",
                mechanism="mech",
                recommendation="rec",
                evidence_note="note",
                related_drugs=["硝苯地平", "布洛芬"],
                related_diseases=["高血压"],
            )
        ],
    )
    result = to_dict(summary)
    assert result["findings"][0]["title"] == "可能影响血压控制"


def test_to_json_outputs_chinese() -> None:
    drug = DrugInfo(input_name="布洛芬", zh_name="布洛芬", en_name="Ibuprofen")
    result = to_json(drug)
    assert "布洛芬" in result


def test_json_output_can_be_loaded() -> None:
    request = DrugSafetyRequest(current_drugs=["硝苯地平"], new_drug="布洛芬")
    result = to_json(request)
    loaded = json.loads(result)
    assert loaded["current_drugs"] == ["硝苯地平"]

