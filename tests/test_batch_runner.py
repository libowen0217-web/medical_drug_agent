import json
from pathlib import Path

from medical_drug_agent.app.evaluation.batch_runner import BatchCaseRunner


def test_runner_can_process_temp_jsonl(tmp_path: Path) -> None:
    case_file = tmp_path / "cases.jsonl"
    case_file.write_text(
        "\n".join(
            [
                json.dumps(
                    {
                        "case_id": "ok-1",
                        "case_name": "成功案例",
                        "expected_risk_level": "medium",
                        "request": {
                            "current_drugs": ["Nifedipine"],
                            "new_drug": "Ibuprofen",
                            "age": 68,
                            "diseases": ["高血压"],
                            "patient_factors": [],
                            "dose": None,
                        },
                    },
                    ensure_ascii=False,
                ),
                json.dumps(
                    {
                        "case_id": "err-1",
                        "case_name": "错误案例",
                        "expected_status": "error",
                        "expected_error_code": "UNKNOWN_DRUG",
                        "request": {
                            "current_drugs": ["Nifedipine"],
                            "new_drug": "UnknownDrug",
                            "age": 50,
                            "diseases": [],
                            "patient_factors": [],
                            "dose": None,
                        },
                    },
                    ensure_ascii=False,
                ),
            ]
        ),
        encoding="utf-8",
    )

    result = BatchCaseRunner().run_cases(case_file)

    assert result["total"] == 2
    assert result["success_count"] == 1
    assert result["error_count"] == 1


def test_success_case_returns_success(tmp_path: Path) -> None:
    case_file = tmp_path / "cases.jsonl"
    case_file.write_text(
        json.dumps(
            {
                "case_id": "ok-1",
                "case_name": "成功案例",
                "request": {
                    "current_drugs": ["Nifedipine"],
                    "new_drug": "Ibuprofen",
                    "age": 68,
                    "diseases": ["高血压"],
                    "patient_factors": [],
                    "dose": None,
                },
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    result = BatchCaseRunner().run_cases(case_file)

    assert result["cases"][0]["actual_status"] == "success"


def test_error_case_does_not_break_batch(tmp_path: Path) -> None:
    case_file = tmp_path / "cases.jsonl"
    case_file.write_text(
        "\n".join(
            [
                "{bad json",
                json.dumps(
                    {
                        "case_id": "ok-2",
                        "case_name": "仍可继续",
                        "request": {
                            "current_drugs": ["Nifedipine"],
                            "new_drug": "Ibuprofen",
                            "age": 68,
                            "diseases": ["高血压"],
                            "patient_factors": [],
                            "dose": None,
                        },
                    },
                    ensure_ascii=False,
                ),
            ]
        ),
        encoding="utf-8",
    )

    result = BatchCaseRunner().run_cases(case_file)

    assert result["total"] == 2
    assert result["cases"][0]["actual_status"] == "error"
    assert result["cases"][1]["actual_status"] == "success"


def test_expected_risk_level_match_sets_true(tmp_path: Path) -> None:
    case_file = tmp_path / "cases.jsonl"
    case_file.write_text(
        json.dumps(
            {
                "case_id": "ok-1",
                "case_name": "风险匹配",
                "expected_risk_level": "medium",
                "request": {
                    "current_drugs": ["Nifedipine"],
                    "new_drug": "Ibuprofen",
                    "age": 68,
                    "diseases": ["高血压"],
                    "patient_factors": [],
                    "dose": None,
                },
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    result = BatchCaseRunner().run_cases(case_file)

    assert result["cases"][0]["matched_expected"] is True


def test_expected_error_code_match_sets_true(tmp_path: Path) -> None:
    case_file = tmp_path / "cases.jsonl"
    case_file.write_text(
        json.dumps(
            {
                "case_id": "err-1",
                "case_name": "错误码匹配",
                "expected_status": "error",
                "expected_error_code": "INVALID_INPUT",
                "request": {
                    "current_drugs": [],
                    "new_drug": "Ibuprofen",
                    "age": 50,
                    "diseases": [],
                    "patient_factors": [],
                    "dose": None,
                },
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    result = BatchCaseRunner().run_cases(case_file)

    assert result["cases"][0]["matched_expected"] is True
