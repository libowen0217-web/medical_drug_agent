from medical_drug_agent.ui.ui_helpers import (
    agent_name_to_label,
    build_drug_safety_payload,
    build_symptom_consult_payload,
    extract_api_ready_data,
    final_level_to_label,
    format_agent_list,
    get_nested,
    risk_level_to_color,
    risk_level_to_label,
    split_multivalue_text,
    validate_patient_context,
)


def test_split_multivalue_text_parses_comma_semicolon_and_newline() -> None:
    assert split_multivalue_text("布洛芬, 对乙酰氨基酚；硝苯地平\n华法林") == [
        "布洛芬",
        "对乙酰氨基酚",
        "硝苯地平",
        "华法林",
    ]


def test_risk_level_to_label_medium_returns_chinese_label() -> None:
    assert risk_level_to_label("medium") == "中等风险"


def test_risk_level_to_color_high_not_empty() -> None:
    assert risk_level_to_color("high")


def test_final_level_to_label_preferred_does_not_contain_recommend_word() -> None:
    assert "推荐" not in final_level_to_label("preferred_candidate")


def test_agent_name_to_label_returns_chinese_label() -> None:
    assert agent_name_to_label("symptom-fit-agent") == "症状匹配智能体"


def test_validate_patient_context_child_cannot_be_elderly() -> None:
    can_submit, _, errors = validate_patient_context(10, "男", ["老年人"])
    assert can_submit is False
    assert errors


def test_validate_patient_context_elderly_cannot_be_child() -> None:
    can_submit, _, errors = validate_patient_context(70, "女", ["儿童"])
    assert can_submit is False
    assert errors


def test_validate_patient_context_male_cannot_be_pregnant() -> None:
    can_submit, _, errors = validate_patient_context(30, "男", ["孕妇"])
    assert can_submit is False
    assert errors


def test_validate_patient_context_elderly_female_can_pass() -> None:
    can_submit, warnings, errors = validate_patient_context(68, "女", ["老年人"])
    assert can_submit is True
    assert warnings
    assert errors == []


def test_build_drug_safety_payload_builds_required_fields() -> None:
    payload = build_drug_safety_payload(
        current_drugs_text=["硝苯地平", "阿司匹林"],
        new_drug="布洛芬",
        age=68,
        diseases_text=["高血压"],
        patient_factors_text=["老年人"],
        include_dose=False,
    )
    assert payload["current_drugs"] == ["硝苯地平", "阿司匹林"]
    assert payload["new_drug"] == "布洛芬"
    assert payload["age"] == 68
    assert payload["diseases"] == ["高血压"]
    assert payload["patient_factors"] == ["老年人"]


def test_build_symptom_consult_payload_builds_required_fields() -> None:
    payload = build_symptom_consult_payload(
        symptom_text="发热、头痛",
        age=68,
        sex="unknown",
        temperature_c=38.5,
        duration_days=2,
        current_drugs_text=["硝苯地平"],
        diseases_text=["高血压"],
        patient_factors_text=["老年人"],
        allergies_text=[],
    )
    assert payload["symptom_text"] == "发热、头痛"
    assert payload["current_drugs"] == ["硝苯地平"]
    assert payload["diseases"] == ["高血压"]
    assert payload["patient_factors"] == ["老年人"]


def test_extract_api_ready_data_parses_success_response() -> None:
    payload = {
        "request_id": "r1",
        "timestamp": "2026-01-01T00:00:00+00:00",
        "status": "success",
        "error_code": None,
        "message": "ok",
        "data": {"x": 1},
        "metadata": {"engine_version": "local-csv-mvp-v1"},
    }
    extracted = extract_api_ready_data(payload)
    assert extracted["status"] == "success"
    assert extracted["data"]["x"] == 1


def test_get_nested_returns_default_for_missing_path() -> None:
    assert get_nested({"a": {"b": 1}}, ["a", "c"], default="missing") == "missing"


def test_format_agent_list_formats_agents_executed() -> None:
    assert "症状匹配智能体" in format_agent_list(["symptom-fit-agent", "evidence-review-agent"])
